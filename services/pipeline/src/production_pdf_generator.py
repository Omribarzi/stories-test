#!/usr/bin/env python3
"""
Production PDF Generator - יצירת PDF ברמת ייצור
עם RTL נכון, ניקוד, ופונטים מקצועיים
"""
import sys
from pathlib import Path
from typing import Dict, List
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from PIL import Image
import os

# Import our custom processors
from hebrew_text_processor import HebrewTextProcessor


class ProductionPDFGenerator:
    """
    מחלקה ליצירת PDF מקצועי לספרי ילדים
    """

    # Hebrew fonts for children (in order of preference)
    CHILD_FRIENDLY_FONTS = [
        # Frank Ruehl - קלאסי וקריא
        {
            "name": "FrankRuehl",
            "paths": [
                "/System/Library/Fonts/Supplemental/FrankRuhlHofshi.ttf",
                "/Library/Fonts/FrankRuehlHofshi.ttf"
            ]
        },
        # Rubik - מודרני וידידותי
        {
            "name": "Rubik",
            "paths": [
                "/System/Library/Fonts/Supplemental/Rubik-Regular.ttf",
                "/Library/Fonts/Rubik-Regular.ttf"
            ]
        },
        # Arial as fallback
        {
            "name": "Arial",
            "paths": [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/Library/Fonts/Arial.ttf"
            ]
        }
    ]

    def __init__(self, output_path: str):
        """
        Args:
            output_path: נתיב לקובץ PDF פלט
        """
        self.output_path = output_path
        self.canvas = canvas.Canvas(str(output_path), pagesize=landscape(A4))
        self.page_width, self.page_height = landscape(A4)
        self.text_processor = HebrewTextProcessor()
        self.hebrew_font = self._load_font()

    def _load_font(self) -> str:
        """
        טוען פונט עברי מתאים לילדים
        """
        for font_config in self.CHILD_FRIENDLY_FONTS:
            for font_path in font_config["paths"]:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_config["name"], font_path))
                        print(f"✅ טעון פונט: {font_config['name']} ({font_path})")
                        return font_config["name"]
                    except Exception as e:
                        print(f"⚠️  שגיאה בטעינת {font_config['name']}: {e}")
                        continue

        print("⚠️  לא נמצא פונט עברי, משתמש ב-Helvetica")
        return 'Helvetica'

    def add_cover_page(self,
                      title: str,
                      subtitle: str,
                      age_range: str,
                      cover_image_path: Path = None):
        """
        יוצר עמוד כריכה מקצועי
        """
        print(f"\n📄 יוצר כריכה...")

        # רקע צבעוני
        self.canvas.setFillColorRGB(0.95, 0.95, 0.98)
        self.canvas.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)

        # כותרת
        self.canvas.setFont(self.hebrew_font, 48)
        self.canvas.setFillColorRGB(0.2, 0.3, 0.6)
        title_display = self.text_processor.process_for_pdf(title)
        title_width = self.canvas.stringWidth(title_display, self.hebrew_font, 48)
        self.canvas.drawString((self.page_width - title_width) / 2, self.page_height - 150, title_display)

        # תת-כותרת
        self.canvas.setFont(self.hebrew_font, 24)
        self.canvas.setFillColorRGB(0.4, 0.4, 0.4)
        subtitle_display = self.text_processor.process_for_pdf(subtitle)
        subtitle_width = self.canvas.stringWidth(subtitle_display, self.hebrew_font, 24)
        self.canvas.drawString((self.page_width - subtitle_width) / 2, self.page_height - 200, subtitle_display)

        # תמונת כריכה (אם יש)
        if cover_image_path and cover_image_path.exists():
            img = Image.open(cover_image_path)
            img_width, img_height = img.size
            aspect = img_height / img_width

            display_width = 400
            display_height = display_width * aspect

            x = (self.page_width - display_width) / 2
            y = 100

            self.canvas.drawImage(str(cover_image_path), x, y,
                                width=display_width, height=display_height,
                                preserveAspectRatio=True, mask='auto')

        # מידע נוסף
        self.canvas.setFont(self.hebrew_font, 14)
        self.canvas.setFillColorRGB(0.5, 0.5, 0.5)
        age_text = self.text_processor.process_for_pdf(f"גילאי {age_range}")
        age_width = self.canvas.stringWidth(age_text, self.hebrew_font, 14)
        self.canvas.drawString((self.page_width - age_width) / 2, 60, age_text)

        self.canvas.showPage()

    def add_interior_page(self,
                         page_number: int,
                         text: str,
                         image_path: Path = None):
        """
        יוצר עמוד פנימי עם טקסט מנוקד וסדר RTL נכון
        """
        print(f"   📄 עמוד {page_number}")

        # רקע לבן
        self.canvas.setFillColorRGB(1, 1, 1)
        self.canvas.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)

        # תמונה בצד שמאל
        if image_path and image_path.exists():
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect = img_height / img_width

            # תמונה תופסת 55% מהרוחב
            display_width = self.page_width * 0.55
            display_height = display_width * aspect

            # מרכוז אנכי
            if display_height > self.page_height - 100:
                display_height = self.page_height - 100
                display_width = display_height / aspect

            x_img = 30
            y_img = (self.page_height - display_height) / 2

            self.canvas.drawImage(str(image_path), x_img, y_img,
                                width=display_width, height=display_height,
                                preserveAspectRatio=True, mask='auto')

        # טקסט בצד ימין
        text_x = self.page_width - 40
        text_y = self.page_height - 80

        # מספר עמוד
        self.canvas.setFont(self.hebrew_font, 12)
        self.canvas.setFillColorRGB(0.6, 0.6, 0.6)
        page_label = self.text_processor.process_for_pdf(f"עמוד {page_number}")
        self.canvas.drawRightString(text_x, text_y, page_label)

        # טקסט הסיפור עם ניקוד
        text_y -= 40
        self.canvas.setFont(self.hebrew_font, 18)
        self.canvas.setFillColorRGB(0.1, 0.1, 0.1)

        # חלוקה לשורות - CORRECT WAY
        max_text_width = self.page_width * 0.35
        lines = self.text_processor.split_to_lines(
            text,
            max_text_width,
            self.hebrew_font,
            18,
            self.canvas
        )

        # כתיבת השורות
        line_height = 28
        for line in lines:
            if text_y < 100:
                break
            self.canvas.drawRightString(text_x, text_y, line)
            text_y -= line_height

        self.canvas.showPage()

    def add_back_page(self, story_data: Dict):
        """
        עמוד אחורי עם מידע על הספר
        """
        print(f"   📄 עמוד אחורי")

        self.canvas.setFillColorRGB(0.95, 0.95, 0.98)
        self.canvas.rect(0, 0, self.page_width, self.page_height, fill=True, stroke=False)

        self.canvas.setFont(self.hebrew_font, 24)
        self.canvas.setFillColorRGB(0.3, 0.3, 0.5)
        title = self.text_processor.process_for_pdf("על הספר")
        title_width = self.canvas.stringWidth(title, self.hebrew_font, 24)
        self.canvas.drawString((self.page_width - title_width) / 2, self.page_height - 100, title)

        # מידע
        self.canvas.setFont(self.hebrew_font, 14)
        self.canvas.setFillColorRGB(0.4, 0.4, 0.4)

        info_lines = [
            f"סיפור: {story_data.get('title', '')}",
            f"גיל יעד: {story_data.get('age_range', '5-8')}",
            "",
            "נוצר באמצעות מערכת ייצור מתקדמת",
            "• ניקוד אוטומטי לקריאה קלה",
            "• איורים עקביים ומקצועיים",
            "• טיפוגרפיה מותאמת לילדים"
        ]

        y = self.page_height - 150
        for line in info_lines:
            line_display = self.text_processor.process_for_pdf(line)
            line_width = self.canvas.stringWidth(line_display, self.hebrew_font, 14)
            self.canvas.drawString((self.page_width - line_width) / 2, y, line_display)
            y -= 25

        self.canvas.showPage()

    def save(self):
        """
        שומר את ה-PDF
        """
        self.canvas.save()
        print(f"\n✅ PDF נוצר: {self.output_path}")

        # מידע על הקובץ
        file_size = Path(self.output_path).stat().st_size / 1024 / 1024
        print(f"   גודל: {file_size:.2f} MB")


# Demo
if __name__ == "__main__":
    print("="*60)
    print("📚 Production PDF Generator - Demo")
    print("="*60)

    pdf = ProductionPDFGenerator("test_output.pdf")

    pdf.add_cover_page(
        title="הלילה הגדול של נועה",
        subtitle="סיפור על נועה",
        age_range="5-8"
    )

    pdf.add_interior_page(
        page_number=1,
        text="נועה עמדה מול המראה בחדר האמבטיה. היא הביטה בעיניים החומות הגדולות שלה."
    )

    pdf.add_back_page({
        "title": "הלילה הגדול של נועה",
        "age_range": "5-8"
    })

    pdf.save()

    print("\n💡 פתח את הקובץ:")
    print("   open test_output.pdf")
