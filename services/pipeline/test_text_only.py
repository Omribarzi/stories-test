#!/usr/bin/env python3
"""Test text rendering on white page — no images."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from production_pdf_with_nikud import ProductionPDFWithNikud

OUTPUT_DIR = Path(__file__).parent / "output_3pages"
OUTPUT_DIR.mkdir(exist_ok=True)

PAGES = [
    (1, 'איתי עמד בתור לשתייה. רועי דחף אותו קדימה. "היי!" איתי הסתובב. רועי כבר שתה, טיפות מים זלגו לו על החולצה. הידיים של איתי נקפצו לאגרופים.'),
    (2, 'איתי דחף את רועי חזק. רועי נפל על הברז. המים ריססו לכל הצדדים. "אתה משוגע?" רועי צעק. המורה בהפסקה הגיעה בריצה. "איתי, לכיתה. עכשיו."'),
    (3, 'איתי ישב בכיתה הריקה. הידיים שלו רעדו. בחוץ, הילדים שיחקו כדורגל. הצעקות נשמעו דרך החלון. איתי הסתכל על הידיים שלו. למה הן תמיד עושות את זה?'),
]

pdf_path = OUTPUT_DIR / "text_only_test.pdf"
pdf = ProductionPDFWithNikud(str(pdf_path), target_age=8)

for page_num, text in PAGES:
    print(f"Page {page_num}...")
    pdf.add_story_page(page_num, text, image_path=None)

pdf.save()
print(f"\nPDF: {pdf_path}")
