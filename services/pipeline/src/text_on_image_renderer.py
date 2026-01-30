#!/usr/bin/env python3
"""
Text-on-Image Renderer - משרטט טקסט עברי על תמונות
עם פונטים מקצועיים וניקוד
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional
from hebrew_text_processor import HebrewTextProcessor
import os
from collections import Counter


class TextOnImageRenderer:
    """
    משרטט טקסט עברי מנוקד על תמונות בפונטים מקצועיים
    """

    # פונטים מקצועיים לספרי ילדים (לפי סדר עדיפות)
    # SF Hebrew אינו עובד כראוי עם PIL/Pillow - גורם לסימנים מוזרים
    BEAUTIFUL_FONTS = [
        # Arial Unicode - עובד מצוין עם עברית ב-PIL
        {
            "name": "Arial Unicode",
            "regular": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "bold": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
        },
        # Arial Rounded Bold - עגול וידידותי
        {
            "name": "Arial Rounded",
            "regular": "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
            "bold": "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
        },
        # Arial רגיל
        {
            "name": "Arial",
            "regular": "/System/Library/Fonts/Supplemental/Arial.ttf",
            "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        }
    ]

    def __init__(self):
        self.text_processor = HebrewTextProcessor()
        self.font_config = self._find_available_font()

    def _find_available_font(self) -> dict:
        """מוצא את הפונט הטוב ביותר הזמין במערכת"""
        for font_config in self.BEAUTIFUL_FONTS:
            if os.path.exists(font_config["regular"]):
                print(f"✅ נמצא פונט: {font_config['name']}")
                return font_config

        print("⚠️  לא נמצא פונט עברי מקצועי")
        return {
            "name": "Default",
            "regular": None,
            "bold": None
        }

    def load_font(self, size: int, bold: bool = False) -> Optional[ImageFont.FreeTypeFont]:
        """טוען פונט בגודל מסוים"""
        try:
            font_path = self.font_config["bold"] if bold else self.font_config["regular"]
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"⚠️  שגיאה בטעינת פונט: {e}")

        # Fallback to default
        return ImageFont.load_default()

    def extract_dominant_color(self, image_path: Path, position: str = "bottom-left") -> Tuple[int, int, int]:
        """
        מחלץ את הצבע הדומיננטי מאיזור מסוים בתמונה

        Args:
            image_path: נתיב לתמונה
            position: מיקום לדגימה - "bottom-left", "top-right", etc.

        Returns:
            צבע RGB דומיננטי
        """
        img = Image.open(image_path).convert('RGB')
        width, height = img.size

        # קבע איזור לדגימה (10% מהתמונה)
        sample_w = width // 10
        sample_h = height // 10

        if position == "bottom-left":
            box = (0, height - sample_h, sample_w, height)
        elif position == "top-right":
            box = (width - sample_w, 0, width, sample_h)
        elif position == "top-left":
            box = (0, 0, sample_w, sample_h)
        else:
            box = (0, height - sample_h, sample_w, height)

        # דגום צבעים מהאיזור
        region = img.crop(box)
        pixels = list(region.getdata())

        # מצא את הצבע הנפוץ ביותר
        color_counter = Counter(pixels)
        dominant_color = color_counter.most_common(1)[0][0]

        return dominant_color

    def calculate_optimal_font_size(self, text: str, max_width: int = 300,
                                    min_font: int = 22, max_font: int = 36) -> int:
        """
        מחשב גודל פונט אידאלי לפי אורך הטקסט

        Args:
            text: הטקסט לבדיקה
            max_width: רוחב מקסימלי זמין
            min_font: גודל פונט מינימלי
            max_font: גודל פונט מקסימלי

        Returns:
            גודל פונט מומלץ
        """
        # ספור מילים ותווים
        num_words = len(text.split())
        num_chars = len(text.strip())

        # חישוב לפי מספר מילים (עיקרי)
        if num_words <= 8:
            # טקסט קצר מאוד - פונט גדול
            return max_font
        elif num_words <= 15:
            # טקסט קצר - פונט בינוני-גדול
            return max_font - 4
        elif num_words <= 25:
            # טקסט בינוני - פונט בינוני
            return max_font - 8
        elif num_words <= 35:
            # טקסט ארוך - פונט קטן
            return min_font + 2
        else:
            # טקסט ארוך מאוד - פונט מינימלי
            return min_font

    def add_text_to_image(self,
                         image_path: Path,
                         text: str,
                         output_path: Path,
                         position: str = "top-right",
                         font_size: int = 48,
                         text_color: Tuple[int, int, int] = (0, 0, 0),
                         bg_color: Optional[Tuple[int, int, int, int]] = None,
                         max_width: int = 500,
                         padding: int = 40,
                         use_nikud: bool = False) -> Path:
        """
        מוסיף טקסט על תמונה קיימת

        Args:
            image_path: נתיב לתמונה המקורית
            text: טקסט עברי
            output_path: נתיב לשמירת התוצאה
            position: מיקום הטקסט - "top-right", "top-left", "bottom-right", etc.
            font_size: גודל הפונט
            text_color: צבע הטקסט (RGB)
            bg_color: צבע רקע אופציונלי (RGBA) למסגרת טקסט
            max_width: רוחב מקסימלי לטקסט
            padding: ריווח מהקצוות
            use_nikud: האם להוסיף ניקוד (מומלץ רק אם הפונט תומך)

        Returns:
            נתיב לתמונה החדשה
        """
        # טען תמונה
        img = Image.open(image_path).convert('RGBA')
        width, height = img.size

        # צור שכבת טקסט
        txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        # טען פונט
        font = self.load_font(font_size, bold=False)

        # הוסף ניקוד רק אם התבקש
        if use_nikud:
            text_with_nikud = self.text_processor.add_nikud(text)
        else:
            text_with_nikud = text

        # חלק לשורות והחל bidi על כל שורה בנפרד
        lines = self._split_text_to_lines_with_bidi(text_with_nikud, font, max_width, draw)

        # חשב גובה שורה קבוע (1.3 פעמים גודל הפונט - צפוף יותר)
        line_height = int(font_size * 1.3)

        # חשב גובה כולל של הטקסט עם מרווח אחיד
        total_height = len(lines) * line_height

        # קבע מיקום התחלתי
        if position == "top-right":
            x = width - max_width - padding
            y = padding
            align = "right"
        elif position == "top-left":
            x = padding
            y = padding
            align = "left"
        elif position == "bottom-right":
            x = width - max_width - padding
            y = height - total_height - padding
            align = "right"
        elif position == "bottom-left":
            x = padding
            y = height - total_height - padding
            align = "right"  # עברית = RTL, מיושר ימינה
        elif position == "center":
            x = (width - max_width) // 2
            y = (height - total_height) // 2
            align = "center"
        else:
            # ברירת מחדל - bottom-left
            x = padding
            y = height - total_height - padding
            align = "left"

        # רקע אופציונלי לטקסט
        if bg_color:
            bg_rect = [
                x - 20, y - 20,
                x + max_width + 20, y + total_height + 20
            ]
            draw.rounded_rectangle(bg_rect, radius=15, fill=bg_color)

        # צייר כל שורה
        current_y = y
        for line in lines:
            bbox = self._get_text_bbox(line, font, draw)
            line_width = bbox[2]

            # מיקום X לפי יישור
            if align == "right":
                line_x = x + max_width - line_width
            elif align == "center":
                line_x = x + (max_width - line_width) // 2
            else:
                line_x = x

            # הצללה (shadow) לקריאות
            shadow_color = (0, 0, 0, 100) if sum(text_color) > 300 else (255, 255, 255, 100)
            draw.text((line_x + 2, current_y + 2), line, font=font, fill=shadow_color)

            # טקסט עצמו
            draw.text((line_x, current_y), line, font=font, fill=text_color + (255,))

            # עבור לשורה הבאה עם מרווח אחיד
            current_y += line_height

        # שלב שכבות
        img = Image.alpha_composite(img, txt_layer)

        # המר ל-RGB ושמור
        final_img = img.convert('RGB')
        final_img.save(output_path, 'PNG', quality=95)

        return output_path

    def _split_text_to_lines_with_bidi(self, text: str, font: ImageFont.FreeTypeFont,
                                        max_width: int, draw: ImageDraw.Draw) -> list:
        """
        מחלק טקסט לשורות והחל bidi transformation על כל שורה
        CRITICAL: פיצול לפני bidi, ואז bidi על כל שורה בנפרד!
        עברית לא צריכה reshaping - רק bidi!
        """
        from bidi.algorithm import get_display

        words = text.split()
        lines_raw = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])

            # החל bidi זמנית לבדיקת רוחב (ללא reshape!)
            test_line_display = get_display(test_line)
            bbox = self._get_text_bbox(test_line_display, font, draw)

            if bbox[2] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines_raw.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines_raw.append(' '.join(current_line))

        # החל bidi על כל שורה בנפרד (ללא reshape!)
        lines_processed = []
        for line in lines_raw:
            bidi_text = get_display(line)
            lines_processed.append(bidi_text)

        return lines_processed

    def _split_text_to_lines(self, text: str, font: ImageFont.FreeTypeFont,
                             max_width: int, draw: ImageDraw.Draw) -> list:
        """מחלק טקסט לשורות לפי רוחב מקסימלי (ללא bidi)"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = self._get_text_bbox(test_line, font, draw)

            if bbox[2] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _get_text_bbox(self, text: str, font: ImageFont.FreeTypeFont,
                       draw: ImageDraw.Draw) -> Tuple[int, int, int, int]:
        """מחשב את גבולות הטקסט"""
        bbox = draw.textbbox((0, 0), text, font=font)
        return (bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1])


# Demo
if __name__ == "__main__":
    print("="*60)
    print("🎨 Text-on-Image Renderer - Demo")
    print("="*60)

    renderer = TextOnImageRenderer()

    test_text = "נועה עמדה מול המראה בחדר האמבטיה. היא הביטה בעיניים החומות הגדולות שלה."

    print(f"\n✅ פונט זמין: {renderer.font_config['name']}")
    print(f"   טקסט לדוגמה: {test_text[:50]}...")
