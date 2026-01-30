#!/usr/bin/env python3
"""
Hebrew Nikud Renderer - מנגנון לציור ניקוד מדויק מעל אותיות
"""
import unicodedata
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import letter


class HebrewNikudRenderer:
    """
    מנגנון שמצייר טקסט עברי עם ניקוד ממורכז נכון
    """

    # טווחי תווים עברי
    HEBREW_LETTERS = range(0x05D0, 0x05EB)  # א-ת
    NIKUD_MARKS = range(0x0591, 0x05C8)  # תווי ניקוד עברי

    # ניקוד שצריך להיות מעל האות
    NIKUD_ABOVE = {
        '\u05B9',  # חולם (ֹ)
        '\u05C2',  # Sin dot
        '\u05C1',  # Shin dot
    }

    # ניקוד שצריך להיות מתחת האות (רוב הניקוד)
    NIKUD_BELOW = {
        '\u05B0',  # שוא (ְ)
        '\u05B1',  # חטף סגול (ֱ)
        '\u05B2',  # חטף פתח (ֲ)
        '\u05B3',  # חטף קמץ (ֳ)
        '\u05B4',  # חיריק (ִ)
        '\u05B5',  # צירה (ֵ)
        '\u05B6',  # סגול (ֶ)
        '\u05B7',  # פתח (ַ)
        '\u05B8',  # קמץ (ָ)
        '\u05BB',  # קובוץ (ֻ)
        '\u05BC',  # דגש (ּ)
        '\u05C7',  # קמץ קטן
    }

    @staticmethod
    def separate_letters_and_nikud(text: str) -> list:
        """
        מפריד טקסט לרשימה של (אות, ניקוד)

        Returns:
            רשימה של tuples: [(אות, ניקוד או None), ...]
        """
        # Normalize ל-NFD כדי להפריד אותיות מניקוד
        nfd_text = unicodedata.normalize('NFD', text)

        result = []
        i = 0
        while i < len(nfd_text):
            char = nfd_text[i]

            # בדוק אם זו אות עברית
            if ord(char) in HebrewNikudRenderer.HEBREW_LETTERS:
                # בדוק אם יש ניקוד אחריה
                nikud = None
                if i + 1 < len(nfd_text):
                    next_char = nfd_text[i + 1]
                    if ord(next_char) in HebrewNikudRenderer.NIKUD_MARKS:
                        nikud = next_char
                        i += 1  # דלג על הניקוד

                result.append((char, nikud))
            else:
                # תו שאינו אות עברית (רווח, סימן פיסוק וכו')
                result.append((char, None))

            i += 1

        return result

    @staticmethod
    def draw_text_with_nikud_pdf(canvas_obj, x, y, text: str, font_name: str,
                                  font_size: int, nikud_offset_ratio: float = 0.65):
        """
        מצייר טקסט עם ניקוד ב-PDF

        Args:
            canvas_obj: ReportLab canvas
            x, y: מיקום התחלתי (baseline)
            text: טקסט עברי עם ניקוד
            font_name: שם הפונט
            font_size: גודל הפונט
            nikud_offset_ratio: יחס ההיסט של הניקוד מעל האות (0.65 = 65% מגובה הפונט מעל baseline)
        """
        # הפרד אותיות וניקוד
        letters_and_nikud = HebrewNikudRenderer.separate_letters_and_nikud(text)

        # הפוך את הסדר ל-RTL (ימין לשמאל)
        letters_and_nikud.reverse()

        # מיקום נוכחי
        current_x = x

        for letter, nikud in letters_and_nikud:
            # צייר את האות
            canvas_obj.setFont(font_name, font_size)
            canvas_obj.drawString(current_x, y, letter)

            # חשב רוחב האות
            letter_width = canvas_obj.stringWidth(letter, font_name, font_size)

            # אם יש ניקוד, צייר אותו ממורכז במיקום הנכון
            if nikud:
                # חשב את מיקום הניקוד - הגדלנו מ-0.70 ל-0.95
                nikud_size = font_size * 0.95  # ניקוד גדול משמעותית כדי שיהיה קריא
                nikud_width = canvas_obj.stringWidth(nikud, font_name, nikud_size)

                # היסט משתנה לפי סוג האות והניקוד
                # כל אות צריכה כיוונון אופטי משלה
                if letter == 'ד':
                    # ד' - כמעט בלי היסט (הכי ימינה)
                    horizontal_offset = nikud_size * 0.0
                elif letter == 'ר':
                    # ר' - כמעט בלי היסט (יותר ימינה)
                    horizontal_offset = nikud_size * 0.01
                elif letter == 'ל':
                    # ל' - היסט בינוני
                    horizontal_offset = nikud_size * 0.10
                elif letter == 'ז':
                    # ז' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'ה':
                    # ה' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'י':
                    # י' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'ג':
                    # ג' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'ש':
                    # ש' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'ח':
                    # ח' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'ב':
                    # ב' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'פ':
                    # פ' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'כ':
                    # כ' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'נ':
                    # נ' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'א':
                    # א' - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.12
                elif letter == 'ו' and nikud in HebrewNikudRenderer.NIKUD_ABOVE:
                    # ו' עם חולם (מעל) - היסט גדול מאוד
                    horizontal_offset = nikud_size * 0.20
                elif letter == 'ו':
                    # ו' עם ניקוד מתחת - היסט גדול (יותר שמאלה)
                    horizontal_offset = nikud_size * 0.18
                else:
                    # אותיות רגילות
                    horizontal_offset = nikud_size * 0.08

                nikud_x = current_x + (letter_width - nikud_width) / 2 - horizontal_offset

                # בדוק אם הניקוד צריך להיות מעל או מתחת
                if nikud in HebrewNikudRenderer.NIKUD_ABOVE:
                    # ניקוד מעל האות (חולם וכו') - קרוב יותר לאות
                    nikud_y = y + font_size * 0.45
                else:
                    # ניקוד מתחת האות (קמץ, פתח, וכו') - מתחת לקו הבסיס
                    nikud_y = y - font_size * 0.05

                canvas_obj.setFont(font_name, nikud_size)
                canvas_obj.drawString(nikud_x, nikud_y, nikud)

            # התקדם למיקום הבא
            current_x += letter_width

        return current_x  # החזר את המיקום הסופי

    @staticmethod
    def draw_centered_text_with_nikud_pdf(canvas_obj, center_x, y, text: str,
                                          font_name: str, font_size: int,
                                          nikud_offset_ratio: float = 0.65):
        """
        מצייר טקסט ממורכז עם ניקוד ב-PDF

        Args:
            canvas_obj: ReportLab canvas
            center_x: מרכז העמוד (X)
            y: מיקום Y
            text: טקסט עברי עם ניקוד
            font_name: שם הפונט
            font_size: גודל הפונט
            nikud_offset_ratio: יחס ההיסט של הניקוד
        """
        # הפרד אותיות וניקוד
        letters_and_nikud = HebrewNikudRenderer.separate_letters_and_nikud(text)

        # הפוך את הסדר ל-RTL
        letters_and_nikud.reverse()

        # חשב את הרוחב הכולל של הטקסט (ללא ניקוד)
        total_width = 0
        for letter, _ in letters_and_nikud:
            total_width += canvas_obj.stringWidth(letter, font_name, font_size)

        # מיקום התחלה (מרכז פחות חצי רוחב)
        start_x = center_x - total_width / 2

        # צייר את הטקסט עם ניקוד
        HebrewNikudRenderer.draw_text_with_nikud_pdf(
            canvas_obj, start_x, y, text, font_name, font_size, nikud_offset_ratio
        )


# Test
if __name__ == "__main__":
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    print("🧪 Testing Hebrew Nikud Renderer")

    # נסה לטעון פונט עברי
    font_path = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("ArialUnicode", font_path))
        font_name = "ArialUnicode"
    else:
        font_name = "Helvetica"

    # צור PDF לבדיקה
    c = pdf_canvas.Canvas("test_nikud.pdf", pagesize=letter)
    page_width, page_height = letter

    # טקסט לבדיקה עם ניקוד
    test_text = "הַלַּיְלָה הַגָּדוֹל שֶׁל אָדָם"

    # צייר את הטקסט ממורכז
    HebrewNikudRenderer.draw_centered_text_with_nikud_pdf(
        c, page_width / 2, page_height - 100, test_text, font_name, 52
    )

    # טקסט רגיל להשוואה (עם get_display)
    from bidi.algorithm import get_display
    bidi_text = get_display(test_text)
    c.setFont(font_name, 52)
    c.drawCentredString(page_width / 2, page_height - 200, bidi_text)

    c.save()
    print(f"✅ נוצר קובץ: test_nikud.pdf")
    print(f"   פונט: {font_name}")
    print(f"   השווה בין הטקסט העליון (מנגנון חדש) לתחתון (ישן)")
