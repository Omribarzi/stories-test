#!/usr/bin/env python3
"""
Generate 3 pages of "הידיים של איתי" as a book:
- Image per page (Gemini)
- PDF with nikud
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from image_generator import ImageGenerator
from production_pdf_with_nikud import ProductionPDFWithNikud

OUTPUT_DIR = Path(__file__).parent / "output_3pages"
OUTPUT_DIR.mkdir(exist_ok=True)
TARGET_AGE = 8

PAGES = [
    {
        "page_num": 1,
        "text": 'איתי עמד בתור לשתייה. רועי דחף אותו קדימה. "היי!" איתי הסתובב. רועי כבר שתה, טיפות מים זלגו לו על החולצה. הידיים של איתי נקפצו לאגרופים.',
        "visual_prompt": """Children's book illustration, page 1 of a story about a boy named Itai.

SCENE: A school water fountain area during recess. An 8-year-old boy (Itai) stands in line at a drinking fountain. Another boy (Roi) has just pushed past him. Roi is already drinking, water droplets on his shirt. Itai is turning around with clenched fists, looking frustrated.

COMPOSITION:
- Main action on the LEFT 60% of the image
- RIGHT 35% must be a soft, calm gradient area (light warm beige/cream) with NO characters, NO objects — reserved for Hebrew text overlay
- 4:3 aspect ratio, 1024x768

STYLE: Modern children's book illustration, soft watercolor-digital hybrid, warm school colors (yellow walls, blue fountain), expressive faces, slightly exaggerated body language. Think Oliver Jeffers meets Einat Tsarfati.

IMPORTANT: No text, no letters, no captions, no watermarks. The right side MUST be empty/calm for text placement."""
    },
    {
        "page_num": 2,
        "text": 'איתי דחף את רועי חזק. רועי נפל על הברז. המים ריססו לכל הצדדים. "אתה משוגע?" רועי צעק. המורה בהפסקה הגיעה בריצה. "איתי, לכיתה. עכשיו."',
        "visual_prompt": """Children's book illustration, page 2 of a story about a boy named Itai.

SCENE: The moment of conflict at the school water fountain. Itai has just pushed Roi hard. Roi is falling against the fountain, water spraying everywhere in dynamic splashes. A teacher is running toward them from the background, looking stern. Other kids are watching with wide eyes.

COMPOSITION:
- Dynamic action scene on the LEFT 60%
- Water splashing adds energy and movement
- RIGHT 35% must be a soft, calm gradient area (light warm beige/cream) with NO characters, NO objects — reserved for Hebrew text overlay
- 4:3 aspect ratio, 1024x768

STYLE: Modern children's book illustration, soft watercolor-digital hybrid, capturing the chaos of the moment. Water droplets flying. Warm school colors but with tension in the body language. Expressive, slightly exaggerated poses.

IMPORTANT: No text, no letters, no captions, no watermarks. The right side MUST be empty/calm for text placement."""
    },
    {
        "page_num": 3,
        "text": 'איתי ישב בכיתה הריקה. הידיים שלו רעדו. בחוץ, הילדים שיחקו כדורגל. הצעקות נשמעו דרך החלון. איתי הסתכל על הידיים שלו. למה הן תמיד עושות את זה?',
        "visual_prompt": """Children's book illustration, page 3 of a story about a boy named Itai.

SCENE: Itai sits alone in an empty classroom. He's at a desk, looking down at his own trembling hands with a confused, sad expression. Through the window behind him, you can see a blurry schoolyard where other kids are playing soccer — bright and colorful outside, contrasting with the quiet, still classroom inside.

COMPOSITION:
- Itai sitting alone on the LEFT 60%, small figure in a big empty room — emphasizing loneliness
- Warm sunlight streaming through the window, casting soft shadows
- RIGHT 35% must be a soft, calm gradient area (light warm beige/cream) with NO characters, NO objects — reserved for Hebrew text overlay
- 4:3 aspect ratio, 1024x768

STYLE: Modern children's book illustration, soft watercolor-digital hybrid. Muted warm tones inside (beige, soft yellow), vibrant colors visible through the window. Emotional, quiet mood. Focus on Itai's hands — they are the symbolic center of the story.

IMPORTANT: No text, no letters, no captions, no watermarks. The right side MUST be empty/calm for text placement."""
    },
]


def main():
    print("=" * 60)
    print("  הידיים של איתי — 3 עמודים ראשונים")
    print("=" * 60)

    image_gen = ImageGenerator(provider="nanobana")
    pdf_path = OUTPUT_DIR / "hayedayim_shel_itai_3pages.pdf"
    pdf = ProductionPDFWithNikud(str(pdf_path), target_age=TARGET_AGE)
    pdf.set_fixed_font_size([p["text"] for p in PAGES])

    total_t0 = time.time()

    for page in PAGES:
        pn = page["page_num"]
        print(f"\n--- Page {pn} ---")

        # Generate image
        print(f"  [img] Generating image...")
        t0 = time.time()
        try:
            result = image_gen.generate_image(
                prompt=page["visual_prompt"],
                aspect_ratio="4:3"
            )
            img_time = time.time() - t0
            print(f"  [img] Done in {img_time:.1f}s, provider={result.get('provider')}, model={result.get('model', '?')}")

            img_path = OUTPUT_DIR / f"page_{pn:02d}.png"
            with open(img_path, 'wb') as f:
                f.write(result["image_data"])
            print(f"  [img] Saved: {img_path.name}")

        except Exception as e:
            print(f"  [img] FAILED: {e}")
            img_path = None

        # Add to PDF (with nikud)
        print(f"  [pdf] Adding page with nikud...")
        t0 = time.time()
        try:
            pdf.add_story_page(pn, page["text"], img_path)
            pdf_time = time.time() - t0
            print(f"  [pdf] Done in {pdf_time:.1f}s")
        except Exception as e:
            print(f"  [pdf] FAILED: {e}")
            import traceback
            traceback.print_exc()

    # Save PDF
    pdf.save()
    total_time = time.time() - total_t0
    print(f"\n{'=' * 60}")
    print(f"  PDF saved: {pdf_path}")
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Open: open '{pdf_path}'")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
