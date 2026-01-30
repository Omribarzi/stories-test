#!/usr/bin/env python3
"""
מערכת לעיצוב כריכה מקצועית עם טיפוגרפיה מהממת
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from PIL import Image
import os
from hebrew_text_processor import HebrewTextProcessor
from hebrew_nikud_renderer import HebrewNikudRenderer


class ProfessionalCoverLayout:
    """
    מעצב כריכות מקצועיות לספרי ילדים
    """

    # פונטים לכריכה (bold, עבה, בולט)
    COVER_FONTS = [
        {
            "name": "FrankRuehlBold",
            "paths": [
                "/System/Library/Fonts/Supplemental/FrankRuhlHofshi-Bold.ttf",
            ]
        },
        {
            "name": "Arial",
            "paths": [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            ]
        }
    ]

    def __init__(self, canvas_obj, page_width, page_height):
        self.canvas = canvas_obj
        self.page_width = page_width
        self.page_height = page_height
        self.text_processor = HebrewTextProcessor()
        self.cover_font = self._load_cover_font()

    def _load_cover_font(self) -> str:
        """טוען פונט מתאים לכריכה"""
        for font_config in self.COVER_FONTS:
            for font_path in font_config["paths"]:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_config["name"], font_path))
                        return font_config["name"]
                    except:
                        continue
        return 'Helvetica-Bold'

    def draw_full_bleed_cover(self,
                             cover_image_path: Path,
                             title: str,
                             subtitle: str = "",
                             age_range: str = "5-8"):
        """
        שער full-bleed מקצועי עם תמונה ברקע
        """
        # 1. תמונת רקע full-bleed
        if cover_image_path and cover_image_path.exists():
            img = Image.open(cover_image_path)
            img_width, img_height = img.size
            aspect = img_height / img_width

            # מלא את כל העמוד
            display_width = self.page_width
            display_height = self.page_width * aspect

            # אם התמונה נמוכה מדי, התאם
            if display_height < self.page_height:
                display_height = self.page_height
                display_width = self.page_height / aspect

            # מרכז
            x = (self.page_width - display_width) / 2
            y = (self.page_height - display_height) / 2

            self.canvas.drawImage(str(cover_image_path), x, y,
                                width=display_width, height=display_height,
                                preserveAspectRatio=True, mask='auto')
        else:
            # רקע צבעוני אם אין תמונה
            self.canvas.setFillColorRGB(0.95, 0.95, 0.98)
            self.canvas.rect(0, 0, self.page_width, self.page_height,
                           fill=True, stroke=False)

        # 2. כותרת ראשית - עבד ואז חשב גודל
        font_size = 52
        self.canvas.setFont(self.cover_font, font_size)

        # הוסף ניקוד לכותרת
        title_with_nikud = self.text_processor.add_nikud(title)

        # חשב רוחב משוער (ללא ניקוד, רק אותיות) - עבור הרקע
        title_without_nikud = title
        # החל bidi זמנית לחישוב רוחב
        from bidi.algorithm import get_display
        title_display_temp = get_display(title_without_nikud)
        title_width = self.canvas.stringWidth(title_display_temp, self.cover_font, font_size)
        title_y = self.page_height - 110

        title_area_height = 120

        # חלץ צבעים דומיננטיים מהתמונה לרקע
        # אם יש תמונת רקע, חלץ צבע מהחלק העליון
        if cover_image_path and cover_image_path.exists():
            from PIL import Image as PILImage
            img = PILImage.open(cover_image_path).convert('RGB')
            # דגום מהחלק העליון של התמונה
            sample_height = img.size[1] // 10
            top_area = img.crop((0, 0, img.size[0], sample_height))
            pixels = list(top_area.getdata())

            # חשב צבע ממוצע
            avg_r = sum(p[0] for p in pixels) / len(pixels) / 255
            avg_g = sum(p[1] for p in pixels) / len(pixels) / 255
            avg_b = sum(p[2] for p in pixels) / len(pixels) / 255

            # השתמש בצבע מעט כהה יותר לרקע
            bg_r, bg_g, bg_b = avg_r * 0.7, avg_g * 0.7, avg_b * 0.7
        else:
            # ברירת מחדל
            bg_r, bg_g, bg_b = 0.2, 0.2, 0.4

        # רקע לכותרת - גדול מספיק
        self.canvas.setFillColorRGB(bg_r, bg_g, bg_b)
        self.canvas.setFillAlpha(0.85)

        # תיקון 2: רקע גדול יותר מהכותרת
        frame_width = title_width + 100  # 50px כל צד
        frame_x = (self.page_width - frame_width) / 2
        self.canvas.roundRect(
            frame_x, self.page_height - title_area_height - 40,
            frame_width, title_area_height,
            20, fill=True, stroke=False
        )

        # איפוס שקיפות
        self.canvas.setFillAlpha(1.0)

        # 3. כותרת - תיקון 4: צבע דומה לשער (לא לבן)
        # השתמש בצבע בהיר שמתאים לתמונה
        text_r = min(1.0, avg_r * 1.3 + 0.2) if cover_image_path and cover_image_path.exists() else 1.0
        text_g = min(1.0, avg_g * 1.3 + 0.2) if cover_image_path and cover_image_path.exists() else 1.0
        text_b = min(1.0, avg_b * 1.3 + 0.2) if cover_image_path and cover_image_path.exists() else 1.0

        # מרכז העמוד
        center_x = self.page_width / 2

        # הצללה - משתמש במנגנון ניקוד חדש
        self.canvas.setFillColorRGB(0, 0, 0)
        HebrewNikudRenderer.draw_centered_text_with_nikud_pdf(
            self.canvas, center_x + 3, title_y - 3, title_with_nikud,
            self.cover_font, font_size
        )

        # כותרת עצמה - עם ניקוד ממורכז מדויק
        self.canvas.setFillColorRGB(text_r, text_g, text_b)
        HebrewNikudRenderer.draw_centered_text_with_nikud_pdf(
            self.canvas, center_x, title_y, title_with_nikud,
            self.cover_font, font_size
        )

        # 4. תת-כותרת עם ניקוד
        if subtitle:
            self.canvas.setFont(self.cover_font, 24)
            self.canvas.setFillColorRGB(0.95, 0.95, 1)

            subtitle_display = self.text_processor.process_for_pdf(subtitle, add_nikud=True, apply_bidi=True)
            # ריכוז אוטומטי
            self.canvas.drawCentredString(center_x, title_y - 50, subtitle_display)

        # 5. סימון גיל בתחתית (רק אם יש age_range)
        if age_range:
            self.canvas.setFont(self.cover_font, 16)

            # רקע עגול לסימון גיל - צבע דומה לתמונה
            badge_r = min(1.0, avg_r * 0.8 + 0.2) if cover_image_path and cover_image_path.exists() else 1.0
            badge_g = min(1.0, avg_g * 0.8 + 0.2) if cover_image_path and cover_image_path.exists() else 0.8
            badge_b = min(1.0, avg_b * 0.8 + 0.2) if cover_image_path and cover_image_path.exists() else 0.2

            self.canvas.setFillColorRGB(badge_r, badge_g, badge_b)

            # תיקון 3: לא לכתוב "גילאי" מקדימה
            age_text = self.text_processor.process_for_pdf(age_range, add_nikud=False, apply_bidi=True)
            age_width = self.canvas.stringWidth(age_text, self.cover_font, 16)

            badge_width = age_width + 40
            badge_x = (self.page_width - badge_width) / 2
            badge_y = 40

            self.canvas.roundRect(badge_x, badge_y - 10, badge_width, 40,
                                20, fill=True, stroke=False)

            # טקסט גיל - צבע כהה יותר
            self.canvas.setFillColorRGB(bg_r, bg_g, bg_b)
            age_x = (self.page_width - age_width) / 2
            self.canvas.drawString(age_x, badge_y + 5, age_text)

    def draw_simple_cover_with_image(self,
                                    cover_image_path: Path,
                                    title: str,
                                    subtitle: str = "",
                                    age_range: str = "5-8"):
        """
        שער פשוט יותר - תמונה במרכז עם טקסט מעל ומתחת
        """
        # רקע צבעוני
        self.canvas.setFillColorRGB(0.95, 0.95, 0.98)
        self.canvas.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)

        # כותרת למעלה
        self.canvas.setFont(self.cover_font, 56)
        self.canvas.setFillColorRGB(0.2, 0.3, 0.6)

        # ללא bidi transformation - הפונט מטפל ב-RTL
        title_display = self.text_processor.process_for_pdf(title, add_nikud=False, apply_bidi=True)
        title_width = self.canvas.stringWidth(title_display, self.cover_font, 56)
        title_x = (self.page_width - title_width) / 2

        self.canvas.drawString(title_x, self.page_height - 100, title_display)

        # תמונה במרכז
        if cover_image_path and cover_image_path.exists():
            img = Image.open(cover_image_path)
            img_width, img_height = img.size
            aspect = img_height / img_width

            display_width = self.page_width * 0.8
            display_height = display_width * aspect

            if display_height > self.page_height - 250:
                display_height = self.page_height - 250
                display_width = display_height / aspect

            x = (self.page_width - display_width) / 2
            y = (self.page_height - display_height) / 2 - 20

            # מסגרת לתמונה
            self.canvas.setStrokeColorRGB(0.3, 0.3, 0.5)
            self.canvas.setLineWidth(3)
            self.canvas.rect(x - 5, y - 5, display_width + 10, display_height + 10)

            self.canvas.drawImage(str(cover_image_path), x, y,
                                width=display_width, height=display_height,
                                preserveAspectRatio=True, mask='auto')

        # תת-כותרת למטה
        if subtitle:
            self.canvas.setFont(self.cover_font, 28)
            self.canvas.setFillColorRGB(0.4, 0.4, 0.6)

            # ללא bidi transformation
            subtitle_display = self.text_processor.process_for_pdf(subtitle, add_nikud=False, apply_bidi=True)
            subtitle_width = self.canvas.stringWidth(subtitle_display, self.cover_font, 28)
            subtitle_x = (self.page_width - subtitle_width) / 2

            self.canvas.drawString(subtitle_x, 120, subtitle_display)

        # גיל
        self.canvas.setFont(self.cover_font, 16)
        self.canvas.setFillColorRGB(0.5, 0.5, 0.5)
        # ללא bidi transformation
        age_text = self.text_processor.process_for_pdf(f"גילאי {age_range}", add_nikud=False, apply_bidi=True)
        age_width = self.canvas.stringWidth(age_text, self.cover_font, 16)
        self.canvas.drawString((self.page_width - age_width) / 2, 60, age_text)

    def draw_back_cover(self, summary: str, age_range: str = "5-8", cover_image_path: Path = None, small_illustration: Path = None):
        """
        כריכה אחורית עם תקציר הספר להורים

        Args:
            summary: תקציר הספר
            age_range: טווח גילאים
            cover_image_path: נתיב לתמונת השער (לחילוץ צבעים)
            small_illustration: תמונה קטנה לעיטור (אופציונלי)
        """
        # חלץ צבעים מתמונת השער - כמו בכריכה הקדמית
        if cover_image_path and cover_image_path.exists():
            from PIL import Image as PILImage
            img = PILImage.open(cover_image_path).convert('RGB')
            # דגום מהחלק העליון - כמו בכריכה הקדמית
            sample_height = img.size[1] // 10
            top_area = img.crop((0, 0, img.size[0], sample_height))
            pixels = list(top_area.getdata())

            # חשב צבע ממוצע
            avg_r = sum(p[0] for p in pixels) / len(pixels) / 255
            avg_g = sum(p[1] for p in pixels) / len(pixels) / 255
            avg_b = sum(p[2] for p in pixels) / len(pixels) / 255

            # צבעי רקע - כהה כמו הכריכה הקדמית
            bg_r, bg_g, bg_b = avg_r * 0.7, avg_g * 0.7, avg_b * 0.7

            # טקסט בהיר
            text_r = min(1.0, avg_r * 1.3 + 0.2)
            text_g = min(1.0, avg_g * 1.3 + 0.2)
            text_b = min(1.0, avg_b * 1.3 + 0.2)

            # מסגרת - צבע בינוני
            border_r = avg_r
            border_g = avg_g
            border_b = avg_b
        else:
            # ברירת מחדל
            bg_r, bg_g, bg_b = 0.2, 0.2, 0.4
            text_r, text_g, text_b = 1.0, 1.0, 1.0
            border_r, border_g, border_b = 0.5, 0.5, 0.7

        # רקע בצבע מותאם - פלטה כמו הכריכה הקדמית
        self.canvas.setFillColorRGB(bg_r, bg_g, bg_b)
        self.canvas.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)

        # ללא מסגרת - עיצוב נקי
        margin = 60

        # כותרת "אודות הספר"
        self.canvas.setFont(self.cover_font, 32)
        self.canvas.setFillColorRGB(text_r, text_g, text_b)

        header = self.text_processor.process_for_pdf("אודות הספר", add_nikud=False, apply_bidi=True)
        # ריכוז אוטומטי מדויק
        center_x = self.page_width / 2
        self.canvas.drawCentredString(center_x, self.page_height - 120, header)

        # תקציר - טקסט ארוך עם word wrap (גודל פונט מוקטן)
        self.canvas.setFont(self.cover_font, 16)
        self.canvas.setFillColorRGB(text_r, text_g, text_b)

        # רוחב מקסימלי לטקסט - מלא רוחב
        max_text_width = self.page_width - 2*margin

        # פיצול לשורות - קודם פצל ואז החל bidi על כל שורה
        words = summary.split()  # פיצול המקור, ללא bidi
        lines_raw = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            # החל bidi זמנית לבדיקת רוחב
            test_line_bidi = self.text_processor.process_for_pdf(test_line, add_nikud=False, apply_bidi=True)
            line_width = self.canvas.stringWidth(test_line_bidi, self.cover_font, 16)

            if line_width <= max_text_width:
                current_line = test_line
            else:
                if current_line:
                    lines_raw.append(current_line)
                current_line = word

        if current_line:
            lines_raw.append(current_line)

        # ציור השורות - החל bidi על כל שורה בנפרד
        y_position = self.page_height - 180
        line_height = 24

        for line in lines_raw:
            # החל bidi על השורה
            line_display = self.text_processor.process_for_pdf(line, add_nikud=False, apply_bidi=True)
            self.canvas.drawCentredString(center_x, y_position, line_display)
            y_position -= line_height

        # תמונה ריבועית במרכז מתחת לטקסט
        if small_illustration and small_illustration.exists():
            from PIL import Image as PILImage
            img = PILImage.open(small_illustration)
            img_width, img_height = img.size

            # חיתוך לריבוע - לוקח את החלק המרכזי
            size = min(img_width, img_height)
            left = (img_width - size) // 2
            top = (img_height - size) // 2
            img_square = img.crop((left, top, left + size, top + size))

            # שמירה זמנית
            temp_path = small_illustration.parent / "temp_square.png"
            img_square.save(temp_path)

            # תמונה ריבועית - 180x180px במרכז
            display_width = 180
            display_height = 180

            # מרכז אופקית
            x = (self.page_width - display_width) / 2
            # מתחת לטקסט עם רווח
            y = y_position - display_height - 40

            # ציור במרכז
            self.canvas.drawImage(str(temp_path), x, y,
                                width=display_width, height=display_height,
                                preserveAspectRatio=True, mask='auto')

        # סימון גיל בתחתית
        if age_range:
            self.canvas.setFont(self.cover_font, 16)
            self.canvas.setFillColorRGB(text_r, text_g, text_b)
            age_text = self.text_processor.process_for_pdf(f"מומלץ לגילאי {age_range}", add_nikud=False, apply_bidi=True)
            # ריכוז אוטומטי
            self.canvas.drawCentredString(center_x, 100, age_text)


# Demo
if __name__ == "__main__":
    print("🎨 Professional Cover Layout - Demo")
