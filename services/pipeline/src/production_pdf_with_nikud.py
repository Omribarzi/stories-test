#!/usr/bin/env python3
"""
Production PDF Generator עם ניקוד מדויק
מערכת ייצור מלאה לספרי ילדים
"""
from pathlib import Path
from typing import Dict, Optional
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from PIL import Image
from bidi.algorithm import get_display
import os

from hebrew_text_processor import HebrewTextProcessor
from hebrew_nikud_renderer import HebrewNikudRenderer
from professional_cover_layout import ProfessionalCoverLayout


def calculate_ideal_font_size(age: int, text: str) -> int:
    """
    מחשב גודל פונט אידיאלי בהתאם לגיל וכמות מילים

    Args:
        age: גיל היעד של הספר
        text: הטקסט של העמוד

    Returns:
        גודל פונט בנקודות
    """
    # ספירת מילים
    word_count = len(text.split())

    # גודל בסיס לפי גיל
    if age <= 4:
        base_size = 24
    elif age <= 6:
        base_size = 22
    else:
        base_size = 20

    # התאמה לפי כמות מילים
    if word_count < 15:
        adjustment = 4
    elif word_count < 25:
        adjustment = 2
    elif word_count < 40:
        adjustment = 0
    elif word_count < 60:
        adjustment = -2
    else:
        adjustment = -3

    # חישוב סופי עם גבולות
    final_size = base_size + adjustment
    final_size = max(18, min(30, final_size))  # בין 18 ל-30

    return final_size


def calculate_max_words_per_line(font_size: int) -> int:
    """
    מחשב מקסימום מילים לשורה בהתאם לגודל הפונט

    Args:
        font_size: גודל הפונט בנקודות

    Returns:
        מספר מקסימלי של מילים לשורה
    """
    # פונט גדול = פחות מילים לשורה
    if font_size >= 26:
        return 3  # ילדים צעירים - 3 מילים מקסימום
    elif font_size >= 22:
        return 4  # גיל בינוני - 4 מילים
    elif font_size >= 20:
        return 5  # גיל יותר מבוגר - 5 מילים
    else:
        return 6  # פונט קטן - 6 מילים


class ProductionPDFWithNikud:
    """
    מחלקה ליצירת PDF production עם ניקוד מדויק
    """

    def __init__(self, output_path: str, target_age: int = 4):
        """
        Args:
            output_path: נתיב לקובץ PDF פלט
            target_age: גיל היעד של הספר (לחישוב גודל פונט)
        """
        self.output_path = output_path
        self.target_age = target_age
        # גודל עמוד 4:3 מותאם לאייפד (תואם את התמונות)
        ipad_size = (1024, 768)
        self.canvas = canvas.Canvas(str(output_path), pagesize=ipad_size)
        self.page_width, self.page_height = ipad_size
        self.text_processor = HebrewTextProcessor()
        self.hebrew_font = self._load_font()

    # Base directory for resolving relative font paths
    _BASE_DIR = Path(__file__).resolve().parent.parent

    def _load_font(self) -> str:
        """
        טוען פונט עברי מתאים
        """
        font_configs = [
            # Noto Sans Hebrew - bundled in repo, works in Docker
            {
                "name": "NotoSansHebrew",
                "paths": [
                    "assets/fonts/NotoSansHebrew-Regular.ttf",
                ]
            },
            {
                "name": "FrankRuehl",
                "paths": [
                    "/System/Library/Fonts/Supplemental/FrankRuhlHofshi.ttf",
                    "/Library/Fonts/FrankRuhlHofshi.ttf"
                ]
            },
            {
                "name": "Arial",
                "paths": [
                    "/System/Library/Fonts/Supplemental/Arial.ttf",
                    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                    "/Library/Fonts/Arial.ttf"
                ]
            }
        ]

        for font_config in font_configs:
            for font_path in font_config["paths"]:
                resolved = self._resolve_font_path(font_path)
                if os.path.exists(resolved):
                    try:
                        pdfmetrics.registerFont(TTFont(font_config["name"], resolved))
                        print(f"✅ טעון פונט: {font_config['name']} ({resolved})")
                        return font_config["name"]
                    except Exception as e:
                        print(f"⚠️  שגיאה בטעינת {font_config['name']}: {e}")
                        continue

        print("⚠️  לא נמצא פונט עברי, משתמש ב-Helvetica")
        return 'Helvetica'

    def _resolve_font_path(self, path: str) -> str:
        """Resolve a font path — absolute paths stay as-is, relative paths resolve from _BASE_DIR."""
        p = Path(path)
        if p.is_absolute():
            return str(p)
        return str(self._BASE_DIR / p)

    def add_cover_page(self, title: str, age: int, cover_image: Optional[Path] = None):
        """
        יוצר עמוד כריכה מקצועי
        """
        print(f"\n📄 יוצר כריכה מקצועית...")

        # יצירת כריכה מקצועית
        layout = ProfessionalCoverLayout(self.canvas, self.page_width, self.page_height)

        # כריכה full-bleed עם תמונה ברקע
        layout.draw_full_bleed_cover(
            cover_image_path=cover_image,
            title=title,
            subtitle="",
            age_range=str(age)
        )

        self.canvas.showPage()

    def add_story_page(self, page_num: int, text: str, image_path: Optional[Path] = None):
        """
        יוצר עמוד סיפור עם ניקוד מדויק

        Args:
            page_num: מספר עמוד
            text: טקסט העמוד
            image_path: נתיב לתמונה (אופציונלי)
        """
        print(f"   📄 עמוד {page_num}")
        print(f"   🔍 DEBUG - page {page_num}:")
        print(f"      page_size: {self.page_width}x{self.page_height}")

        # רקע לבן תמיד (קודם כל - למנוע שחור/undefined)
        self.canvas.setFillColorRGB(1, 1, 1)
        self.canvas.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)
        print(f"      background: WHITE (1.0, 1.0, 1.0) - drawn")

        # תמונה FULL BLEED - מותח לגודל העמוד המדויק (אם קיימת)
        if image_path and image_path.exists():
            img = Image.open(image_path)
            img_width, img_height = img.size
            print(f"      image_path: {image_path.name}")
            print(f"      image_size: {img_width}x{img_height}")
            print(f"      fit_mode: STRETCH (preserveAspectRatio=False)")
            print(f"      target: 0,0 → {self.page_width}x{self.page_height}")

            # מותח את התמונה למלא את העמוד בדיוק ללא שוליים
            # קיים עיוות קל ביחס גובה-רוחב (1.370 -> 1.333) אבל עדיף על שוליים לבנים
            self.canvas.drawImage(str(image_path), 0, 0,
                                width=self.page_width, height=self.page_height,
                                preserveAspectRatio=False, mask='auto')
        else:
            print(f"      image_path: NONE (white background only)")

        # טקסט מונח על התמונה בצד ימין
        # התמונה כבר כוללת שטח ריק בצד ימין (40% מהתמונה) לטקסט
        text_area_width = self.page_width * 0.35  # 35% מרוחב העמוד לטקסט
        text_x = self.page_width - 30  # מיישר ימינה עם מרווח קטן מהקצה (30px במקום 60px)
        text_y = self.page_height - 100

        # טקסט הסיפור עם ניקוד - צבע כהה לקריאות
        self.canvas.setFillColorRGB(0, 0, 0)  # שחור מלא לקריאות טובה

        # הוסף ניקוד לטקסט - משתמש ב-Claude API לניקוד מלא
        text_with_nikud = self.text_processor.add_nikud(text, use_api=True)

        # חישוב גודל פונט אידיאלי
        font_size = calculate_ideal_font_size(self.target_age, text)
        line_height = int(font_size * 1.8)  # רווח גדול לניקוד (1.8x גודל הפונט)

        # חישוב מקסימום מילים לשורה לפי גודל פונט
        max_words_per_line = calculate_max_words_per_line(font_size)

        # פצל לפי משפטים
        sentences = text_with_nikud.split('.')

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence = sentence + '.'

            # פצל משפט למילים
            words = sentence.split()
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                # בדיקת רוחב משוערת
                test_display = get_display(test_line)
                line_width = self.canvas.stringWidth(test_display, self.hebrew_font, font_size)

                # בדיקה משולשת: רוחב, מספר מילים, ומספר תווים
                words_in_line = len(current_line) + 1
                chars_in_line = len(test_line)  # כולל רווחים וסימני פיסוק
                max_chars_per_line = 23

                if (line_width <= text_area_width and
                    words_in_line <= max_words_per_line and
                    chars_in_line <= max_chars_per_line):
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # צייר כל שורה עם ניקוד מדויק
            for line in lines:
                if text_y < 100:  # אין מספיק מקום
                    break

                # חשב רוחב השורה
                line_display = get_display(line)
                line_width = self.canvas.stringWidth(line_display, self.hebrew_font, font_size)

                # צייר עם HebrewNikudRenderer
                HebrewNikudRenderer.draw_text_with_nikud_pdf(
                    self.canvas, text_x - line_width, text_y,
                    line, self.hebrew_font, font_size
                )

                text_y -= line_height

        # מספר עמוד בתחתית בצד ימין - רק ספרה
        self.canvas.setFont(self.hebrew_font, 14)
        self.canvas.setFillColorRGB(0.5, 0.5, 0.5)
        page_number_str = str(page_num)
        page_number_display = get_display(page_number_str)
        self.canvas.drawRightString(self.page_width - 40, 30, page_number_display)

        self.canvas.showPage()

    def add_back_page(self, story_title: str, age: int, cover_image: Optional[Path] = None,
                      summary: str = None, small_illustration: Optional[Path] = None):
        """
        עמוד אחורי מקצועי
        """
        print(f"   📄 כריכה אחורית מקצועית")

        # תקציר ברירת מחדל
        if not summary:
            summary = f"סיפור {story_title} - סיפור מקסים לילדים המעודד דמיון, אומץ וערכים חשובים. נוצר עם מערכת ייצור מתקדמת הכוללת ניקוד מדויק, טיפוגרפיה מקצועית ואיכות ייצור גבוהה."

        # יצירת כריכה אחורית מקצועית
        layout = ProfessionalCoverLayout(self.canvas, self.page_width, self.page_height)

        layout.draw_back_cover(
            summary=summary,
            age_range=str(age),
            cover_image_path=cover_image,
            small_illustration=small_illustration
        )

        self.canvas.showPage()

    def save(self):
        """
        שומר את ה-PDF
        """
        self.canvas.save()
        file_size = Path(self.output_path).stat().st_size / 1024 / 1024
        print(f"\n✅ PDF נוצר: {self.output_path}")
        print(f"   גודל: {file_size:.2f} MB")


def create_production_pdf(story_data: Dict, images_dir: Optional[Path], output_path: Path):
    """
    יוצר PDF production מלא

    Args:
        story_data: נתוני הסיפור (JSON)
        images_dir: תיקיית תמונות (אופציונלי)
        output_path: נתיב פלט
    """
    print("="*70)
    print("📚 Production PDF Generator עם ניקוד מדויק")
    print("="*70)

    story = story_data['story']
    title = story['title']
    age = story.get('target_age', 4)
    pages = story['pages']

    print(f"\n📖 סיפור: {title}")
    print(f"   גיל יעד: {age}")
    print(f"   עמודים: {len(pages)}")

    # אתחול PDF generator עם גיל היעד
    pdf = ProductionPDFWithNikud(str(output_path), target_age=age)

    # כריכה - חפש תמונת כריכה ייעודית
    cover_image = None
    if images_dir:
        # אפשרות 1: תמונת כריכה ייעודית (cover_background.png)
        # נסה למצוא בתיקיות שכנות
        base_images_dir = images_dir.parent
        possible_cover_dirs = [
            base_images_dir / "adam_cover",
            base_images_dir / "mia_cover",
            images_dir.parent.parent / "images" / "adam_cover",
            images_dir.parent.parent / "images" / "mia_cover",
            images_dir / "cover"
        ]

        for cover_dir in possible_cover_dirs:
            cover_bg = cover_dir / "cover_background.png"
            if cover_bg.exists():
                cover_image = cover_bg
                print(f"   ✅ נמצאה כריכה ייעודית: {cover_image}")
                break

        # אפשרות 2: אם לא נמצאה כריכה ייעודית, השתמש בעמוד ראשון
        if not cover_image:
            cover_image = images_dir / "page_01_final.png"
            if not cover_image.exists():
                # נסה גרסאות אחרות
                for variant in ["page_01_empty.png", "page_01.png"]:
                    alt = images_dir / variant
                    if alt.exists():
                        cover_image = alt
                        break

            if cover_image and cover_image.exists():
                print(f"   ℹ️  משתמש בעמוד 1 ככריכה: {cover_image}")
            else:
                cover_image = None
                print(f"   ⚠️  לא נמצאה תמונת כריכה")

    pdf.add_cover_page(title, age, cover_image)

    # עמודי סיפור
    for page in pages:
        page_num = page['page_number']
        text = page['text']

        # חפש תמונה - נסה כמה אפשרויות
        image_path = None
        if images_dir:
            # נסה מספר וריאציות של שם הקובץ
            for variant in [
                f"page_{page_num:02d}_final.png",
                f"page_{page_num:02d}_empty.png",
                f"page_{page_num:02d}.png",
                f"page_{page_num}_final.png",
                f"page_{page_num}_empty.png"
            ]:
                candidate = images_dir / variant
                if candidate.exists():
                    image_path = candidate
                    break

            if not image_path:
                print(f"      ⚠️  לא נמצאה תמונה לעמוד {page_num}")
            else:
                print(f"      ✓ תמונה: {image_path.name}")

        # חישוב גודל פונט לעמוד זה
        word_count = len(text.split())
        font_size = calculate_ideal_font_size(age, text)
        print(f"      גודל פונט: {font_size} (מילים: {word_count})")

        pdf.add_story_page(page_num, text, image_path)

    # כריכה אחורית לא רלוונטית לסיפורי אייפד - מדלגים

    # שמירה
    pdf.save()

    return output_path


# Demo
if __name__ == "__main__":
    import json

    story_file = Path("data/stories/נועה_age4/story_generic_20260129_142910.json")
    images_dir = None  # אין תמונות עדיין
    output_pdf = Path("data/output/production_נועה_והפינה_השקטה.pdf")

    if not story_file.exists():
        print(f"❌ קובץ סיפור לא נמצא: {story_file}")
        exit(1)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # טען סיפור
    with open(story_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    # יצירת PDF
    result = create_production_pdf(story_data, images_dir, output_pdf)

    print(f"\n💡 פתח את הקובץ:")
    print(f"   open '{result}'")

    # פתיחה אוטומטית
    import subprocess
    subprocess.run(['open', str(result)])
