#!/usr/bin/env python3
"""
🔍 בדיקת איכות של עמוד בספר
בודק 4 קריטריונים:
1. התמונה ממלאת את הדף (לא רוב הדף לבן)
2. הניקוד מלא לכל המילים
3. הדמות עקבית (תואמת תיאור)
4. הטקסט לא עולה על התמונה (נשאר באזור הריק)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import argparse
from PIL import Image
import fitz  # PyMuPDF
import re


def check_image_fills_page(pdf_path: Path, page_num: int):
    """
    בודק אם התמונה ממלאת את הדף או שיש הרבה לבן
    """
    print(f"\n📐 בדיקה 1: האם התמונה ממלאת את הדף?")

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]

    # רזולוציה גבוהה לדיוק
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

    # המר ל-PIL
    img_data = pix.tobytes("ppm")
    import io
    img = Image.open(io.BytesIO(img_data))

    # בדוק כמה פיקסלים לבנים/בהירים יש
    width, height = img.size
    total_pixels = width * height

    # ספור פיקסלים לבנים (או קרובים ללבן)
    white_count = 0
    pixels = img.convert('RGB')

    # דגימה - בדוק כל 10 פיקסלים
    sample_step = 10
    sampled = 0
    white_sampled = 0

    for x in range(0, width, sample_step):
        for y in range(0, height, sample_step):
            r, g, b = pixels.getpixel((x, y))
            sampled += 1

            # פיקסל נחשב "לבן" אם כל הערוצים מעל 240
            if r > 240 and g > 240 and b > 240:
                white_sampled += 1

    white_percentage = (white_sampled / sampled) * 100 if sampled > 0 else 0

    # קריטריון: אם יותר מ-20% לבן, זה בעייתי
    passed = white_percentage < 20

    if passed:
        print(f"   ✅ עבר - רק {white_percentage:.1f}% מהדף לבן")
    else:
        print(f"   ❌ נכשל - {white_percentage:.1f}% מהדף לבן (צריך פחות מ-20%)")

    doc.close()
    return passed, white_percentage


def check_nikud_coverage(pdf_path: Path, page_num: int):
    """
    בודק אם הניקוד מלא בטקסט
    """
    print(f"\n🔤 בדיקה 2: האם הניקוד מלא?")

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]

    # חלץ טקסט
    text = page.get_text()

    # תווי ניקוד עברי
    nikud_chars = [
        '\u05B0',  # שוא
        '\u05B1',  # חטף סגול
        '\u05B2',  # חטף פתח
        '\u05B3',  # חטף קמץ
        '\u05B4',  # חיריק
        '\u05B5',  # צירה
        '\u05B6',  # סגול
        '\u05B7',  # פתח
        '\u05B8',  # קמץ
        '\u05B9',  # חולם
        '\u05BB',  # קובוץ
        '\u05BC',  # דגש
        '\u05C1',  # shin dot
        '\u05C2',  # sin dot
    ]

    # אותיות עברית
    hebrew_letters = re.findall(r'[\u05D0-\u05EA]', text)

    # תווי ניקוד
    nikud_found = sum(1 for char in text if char in nikud_chars)

    total_hebrew = len(hebrew_letters)

    if total_hebrew == 0:
        print(f"   ⚠️  לא נמצא טקסט עברי בעמוד")
        return False, 0

    # יחס ניקוד לאותיות - לא כל אות צריכה ניקוד, אבל אמור להיות לפחות 30%
    nikud_ratio = (nikud_found / total_hebrew) * 100

    # קריטריון: לפחות 30% מהאותיות עם ניקוד
    passed = nikud_ratio >= 30

    print(f"   אותיות עבריות: {total_hebrew}")
    print(f"   תווי ניקוד: {nikud_found}")
    print(f"   יחס: {nikud_ratio:.1f}%")

    if passed:
        print(f"   ✅ עבר - יחס ניקוד מספיק ({nikud_ratio:.1f}% >= 30%)")
    else:
        print(f"   ❌ נכשל - יחס ניקוד נמוך ({nikud_ratio:.1f}% < 30%)")

        # הדפס דוגמה מהטקסט
        sample_text = text[:200].strip()
        print(f"\n   דוגמה מהטקסט:")
        print(f"   {sample_text}")

    doc.close()
    return passed, nikud_ratio


def check_character_consistency(image_path: Path, character_desc: str):
    """
    בודק אם הדמות תואמת את התיאור (באמצעות ImageValidator)
    """
    print(f"\n👤 בדיקה 3: האם הדמות תואמת את התיאור?")

    from image_validator import ImageValidator

    validator = ImageValidator()

    validation_context = {
        'character_description': character_desc
    }

    passed, reason, details = validator.validate_image(image_path, validation_context)

    # בדוק ספציפית את character_accurate
    char_result = details.get('character_accurate', {})
    char_passed = char_result.get('passed', False)
    char_details = char_result.get('details', 'לא זמין')

    if char_passed:
        print(f"   ✅ עבר - הדמות תואמת")
        print(f"      {char_details[:150]}")
    else:
        print(f"   ❌ נכשל - הדמות לא תואמת")
        print(f"      {char_details[:150]}")

    return char_passed, char_details


def check_text_not_overlapping_image(pdf_path: Path, page_num: int, original_image_path: Path):
    """
    בודק שהטקסט לא עולה על התמונה - ע"י השוואה בין התמונה המקורית לעמוד ב-PDF
    """
    print(f"\n📏 בדיקה 4: האם הטקסט נשאר באזור הריק ולא עולה על התמונה?")

    if not original_image_path.exists():
        print(f"   ⚠️  תמונה מקורית לא נמצאה: {original_image_path}")
        return None, 0

    doc = fitz.open(str(pdf_path))
    page = doc[page_num]

    # המר PDF לתמונה
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    import io
    img_data = pix.tobytes("ppm")
    pdf_image = Image.open(io.BytesIO(img_data))

    # טען תמונה מקורית
    original_image = Image.open(original_image_path)

    # גודל
    pdf_width, pdf_height = pdf_image.size
    orig_width, orig_height = original_image.size

    # בדוק את האזור הימני (40% ימינים) - שם צריך להיות הטקסט
    # נבדוק שבאזור השמאלי (60% שמאליים) אין הבדלים גדולים
    left_60_percent = int(pdf_width * 0.60)

    # דגימת נקודות באזור הציור (60% שמאליים)
    sample_step = 20
    differences = []

    # שנה גודל תמונה מקורית אם צריך
    if (orig_width, orig_height) != (pdf_width, pdf_height):
        original_image = original_image.resize((pdf_width, pdf_height), Image.Resampling.LANCZOS)

    pdf_pixels = pdf_image.convert('RGB')
    orig_pixels = original_image.convert('RGB')

    for x in range(0, left_60_percent, sample_step):
        for y in range(100, pdf_height - 100, sample_step):  # דלג על שוליים
            pdf_r, pdf_g, pdf_b = pdf_pixels.getpixel((x, y))
            orig_r, orig_g, orig_b = orig_pixels.getpixel((x, y))

            # חשב הבדל
            diff = abs(pdf_r - orig_r) + abs(pdf_g - orig_g) + abs(pdf_b - orig_b)
            differences.append(diff)

    # ממוצע הבדלים
    avg_diff = sum(differences) / len(differences) if differences else 0

    # אם ההבדל גבוה מדי - הטקסט עלה על התמונה
    # ערך תקין: פחות מ-30 (טקסט רק באזור הימני)
    passed = avg_diff < 30

    if passed:
        print(f"   ✅ עבר - הטקסט לא עולה על התמונה")
        print(f"      הבדל ממוצע: {avg_diff:.1f} (< 30)")
    else:
        print(f"   ⚠️  חשד - הטקסט אולי עולה על התמונה")
        print(f"      הבדל ממוצע: {avg_diff:.1f} (>= 30)")
        print(f"      האזור הריק לטקסט אולי לא מספיק גדול")

    doc.close()
    return passed, avg_diff


def main():
    parser = argparse.ArgumentParser(description='בודק איכות של עמוד בספר')
    parser.add_argument('pdf_file', type=str, help='נתיב ל-PDF')
    parser.add_argument('--page', type=int, default=1, help='מספר עמוד לבדיקה (1-based)')
    parser.add_argument('--image', type=str, help='נתיב לתמונה המקורית (לבדיקת דמות)')
    parser.add_argument('--character', type=str, default="4-year-old boy with light blonde hair and green eyes",
                       help='תיאור הדמות')

    args = parser.parse_args()

    pdf_path = Path(args.pdf_file)

    if not pdf_path.exists():
        print(f"❌ קובץ לא נמצא: {pdf_path}")
        return 1

    print("="*80)
    print(f"🔍 בדיקת איכות - עמוד {args.page}")
    print("="*80)
    print(f"📄 PDF: {pdf_path.name}")
    print(f"👤 דמות: {args.character}")

    # בדיקה 1: התמונה ממלאת את הדף
    check1_passed, white_pct = check_image_fills_page(pdf_path, args.page - 1)  # 0-based

    # בדיקה 2: ניקוד מלא
    check2_passed, nikud_ratio = check_nikud_coverage(pdf_path, args.page - 1)

    # בדיקה 3: דמות תואמת (אם סיפקו תמונה)
    check3_passed = None
    if args.image:
        image_path = Path(args.image)
        if image_path.exists():
            check3_passed, char_details = check_character_consistency(image_path, args.character)
        else:
            print(f"\n⚠️  תמונה לא נמצאה: {args.image}")

    # בדיקה 4: טקסט לא עולה על התמונה (אם סיפקו תמונה)
    check4_passed = None
    text_overlap_diff = 0
    if args.image:
        image_path = Path(args.image)
        if image_path.exists():
            check4_passed, text_overlap_diff = check_text_not_overlapping_image(pdf_path, args.page - 1, image_path)

    # סיכום
    print("\n" + "="*80)
    print("📊 סיכום")
    print("="*80)

    checks = [
        ("התמונה ממלאת את הדף", check1_passed, f"{white_pct:.1f}% לבן"),
        ("ניקוד מלא", check2_passed, f"{nikud_ratio:.1f}% יחס"),
    ]

    if check3_passed is not None:
        checks.append(("דמות תואמת", check3_passed, ""))

    if check4_passed is not None:
        checks.append(("טקסט לא עולה על תמונה", check4_passed, f"הבדל: {text_overlap_diff:.1f}"))

    for name, passed, detail in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name:30} {detail}")

    all_passed = (check1_passed and check2_passed and
                  (check3_passed if check3_passed is not None else True) and
                  (check4_passed if check4_passed is not None else True))

    print("="*80)
    if all_passed:
        print("✅ כל הבדיקות עברו!")
    else:
        print("❌ יש בעיות שצריך לתקן")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
