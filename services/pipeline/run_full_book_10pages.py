#!/usr/bin/env python3
"""
הפקת ספר מלא של 10 עמודים - כל Stages 1-5
עם edge validation, white threshold, overlap gating
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import json
import hashlib
from datetime import datetime
from PIL import Image
from pathlib import Path

from claude_agent import ClaudeAgent
from image_generator import ImageGenerator
from production_pdf_with_nikud import ProductionPDFWithNikud
from validate_single_page import (
    check_image_fills_page,
    check_nikud_coverage,
    check_text_not_overlapping_image
)


def get_text_area_bounds(image_width: int, image_height: int) -> tuple:
    """
    חישוב גבולות אזור הטקסט - MUST match PDF rendering exactly

    Returns:
        (x_start, y_start, width, height) for text area ROI
    """
    # These values MUST match production_pdf_with_nikud.py exactly
    text_area_width = int(image_width * 0.35)  # 35% of page width
    right_margin = 30  # text_x = page_width - 30 in PDF (הוזז ימינה!)

    # Text area starts where rightmost text edge is, minus the text_area_width
    text_x_start = image_width - right_margin - text_area_width

    # For validation, check the full vertical range where text appears
    # Text is placed from y=100 to y=page_height-100 in PDF
    text_y_start = 100
    text_height = image_height - 200

    return (text_x_start, text_y_start, text_area_width, text_height)


class RunManager:
    """מנהל ריצה עם metadata ולוגים"""

    def __init__(self, child_name: str, age: int, topic: str):
        self.child_name = child_name
        self.age = age
        self.topic = topic
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = hashlib.sha256(f"{timestamp}{child_name}".encode()).hexdigest()[:8]
        self.run_id = f"{timestamp}_{random_id}"

        # תיקיות
        self.base_dir = Path(f"data/runs/{child_name}_age{age}_{topic}/{self.run_id}")
        self.story_dir = self.base_dir / "story"
        self.images_dir = self.base_dir / "images"
        self.pdf_dir = self.base_dir / "pdf"
        self.qa_dir = self.base_dir / "qa"
        self.logs_dir = self.base_dir / "logs"

        for d in [self.story_dir, self.images_dir, self.pdf_dir, self.qa_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_story(self, story_data: dict):
        story_path = self.story_dir / "story.json"
        with open(story_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        return story_path


def step1_generate_story(run: RunManager, num_pages: int = 10):
    """Stage 1: יצירת סיפור"""
    print("\n" + "="*80)
    print(f"📖 Stage 1: Story Generation - {num_pages} עמודים")
    print("="*80)

    agent = ClaudeAgent()

    # בקש סיפור עם מספר עמודים מדויק
    prompt = f"""צור סיפור לספר ילדים ל-{run.child_name} בגיל {run.age} על הנושא: {run.topic}

דרישות:
- בדיוק {num_pages} עמודים (לא יותר, לא פחות)
- כל עמוד עם טקסט ותיאור ויזואלי
- מותאם לגיל {run.age}
- סיפור טוב עם התחלה, אמצע וסוף

פורמט JSON:
{{
  "story": {{
    "title": "כותרת הסיפור",
    "target_age": {run.age},
    "pages": [
      {{
        "page_number": 1,
        "text": "טקסט העמוד...",
        "visual_description": "תיאור מפורט של הסצנה..."
      }},
      ...
    ]
  }}
}}"""

    response = agent.client.messages.create(
        model=agent.model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.content[0].text

    # חלץ JSON
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    story_json = content[json_start:json_end]
    story_data = json.loads(story_json)

    # וודא שיש בדיוק num_pages עמודים
    actual_pages = len(story_data['story']['pages'])
    if actual_pages != num_pages:
        print(f"   ⚠️  נוצרו {actual_pages} עמודים במקום {num_pages}, קוצץ/משלים")
        if actual_pages > num_pages:
            story_data['story']['pages'] = story_data['story']['pages'][:num_pages]
        # אם פחות - נשאר כך (לא משלים)

    story_path = run.save_story(story_data)

    title = story_data['story']['title']
    print(f"\n✅ סיפור נוצר: {title}")
    print(f"   עמודים: {len(story_data['story']['pages'])}")
    print(f"   💾 נשמר: {story_path}")

    return story_data


def step3_generate_images(run: RunManager, story_data: dict, max_retries: int = 3):
    """Stage 3: יצירת תמונות עם edge validation"""
    print("\n" + "="*80)
    print("🎨 Stage 3: Image Generation with Edge Validation")
    print("="*80)

    pages = story_data['story']['pages']
    image_gen = ImageGenerator(provider="nanobana")

    results = []

    for page in pages:
        page_num = page['page_number']
        text = page['text']
        visual_desc = page['visual_description']

        print(f"\n📄 עמוד {page_num}/{len(pages)}")

        # בנה prompt
        prompt = f"""Children's book illustration for page {page_num}.

SCENE (page {page_num})
{visual_desc}

COMPOSITION / LAYOUT (iPad page)
- Aspect ratio: 4:3
- Resolution: 1024x768

IMPORTANT LAYOUT INSTRUCTION:
The illustration must be visually rich and detailed on the LEFT side of the page.
The RIGHT side of the page is reserved for text and must remain visually calm, but NOT empty or plain white.

On the right side:
- Use a soft pastel color gradient or subtle wall texture
- Add gentle visual interest (light brush texture, soft shading)
- Do NOT place any characters, objects, furniture, or strong details on the right side
- Avoid flat white or flat beige areas

The calm right-side area should occupy approximately 30–35% of the image width.

STYLE
High-quality modern children's book illustration, soft painterly digital art, warm gentle palette, clean lines, no photorealism.

NEGATIVE CONSTRAINTS
ABSOLUTELY NO TEXT, LETTERS, NUMBERS, SIGNS, OR LABELS anywhere in the image.
- No text, no letters, no captions, no speech bubbles
- No watermark, no logo, no signature
- No creepy or scary mood
- No exaggerated facial expressions

CRITICAL: Full-bleed illustration extending to all edges. NO borders, NO frames, NO margins."""

        # שמור prompt
        prompt_path = run.logs_dir / f"prompt_page{page_num:02d}.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

        # QA Loop עם edge validation
        attempts = 0
        last_qa_failure = None
        image_path = None

        for attempt in range(1, max_retries + 1):
            attempts = attempt
            print(f"   🔄 ניסיון {attempt}/{max_retries}")

            # הוסף delta prompt אם נכשל קודם
            current_prompt = prompt
            if last_qa_failure:
                if last_qa_failure.get('white_too_high'):
                    delta = "\n\nIMPORTANT: Add subtle warm textures to walls and floor. Use soft beige/light pastel backgrounds instead of pure white."
                    current_prompt += delta
                    print(f"      🔧 Delta: מונע שטחים לבנים")

                if last_qa_failure.get('border_detected'):
                    delta = "\n\nCRITICAL REQUIREMENT: This MUST be a full-bleed illustration that extends to ALL FOUR EDGES of the canvas. NO borders, NO frames, NO margins."
                    current_prompt += delta
                    print(f"      🔧 Delta: מונע borders/frames")

                if last_qa_failure.get('text_area_intrusion'):
                    delta = "\n\nCRITICAL SPATIAL FIX: Push all characters, objects, and scene details further LEFT. The right 30-35% of the canvas is RESERVED FOR TEXT and must remain calm and clean - just plain wall or background. No illustrated content, no furniture, no decorative elements, no high-contrast edges in this right area. The illustration must stay strictly in the LEFT 65-70% of the canvas."
                    current_prompt += delta
                    print(f"      🔧 Delta: מונע פלישה לאזור טקסט")

            # Generate
            result = image_gen.generate_image(
                prompt=current_prompt,
                aspect_ratio="4:3"
            )

            if not result or 'image_data' not in result:
                print(f"      ❌ API נכשל")
                continue

            image_data = result['image_data']

            # שמור זמני
            temp_path = run.images_dir / f"page_{page_num:02d}_attempt{attempt}.png"
            with open(temp_path, 'wb') as f:
                f.write(image_data)

            # QA Checks
            print(f"      🔍 בדיקות QA...")

            # רזולוציה
            with Image.open(temp_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                target_aspect = 4 / 3
                resolution_ok = abs(aspect_ratio - target_aspect) / target_aspect <= 0.05
                print(f"         {'✅' if resolution_ok else '❌'} רזולוציה: {width}x{height}")

            # White percentage
            with Image.open(temp_path) as img:
                rgb_img = img.convert('RGB')
                pixels = rgb_img.getdata()
                white_pixels = sum(1 for r, g, b in pixels if r > 240 and g > 240 and b > 240)
                white_pct = (white_pixels / len(pixels)) * 100
            white_ok = white_pct <= 21.0
            print(f"         {'✅' if white_ok else '❌'} לבן: {white_pct:.1f}%")

            # Edge border detection
            with Image.open(temp_path) as img:
                rgb_img = img.convert('RGB')
                w, h = rgb_img.size
                edge_thickness = 5

                # Sample edges
                top_pixels = [rgb_img.getpixel((x, y)) for x in range(w) for y in range(min(edge_thickness, h))]
                bottom_pixels = [rgb_img.getpixel((x, y)) for x in range(w) for y in range(max(0, h - edge_thickness), h)]
                left_pixels = [rgb_img.getpixel((x, y)) for y in range(h) for x in range(min(edge_thickness, w))]
                right_pixels = [rgb_img.getpixel((x, y)) for y in range(h) for x in range(max(0, w - edge_thickness), w)]

                def is_uniform_color(pixels, tolerance=30):
                    if not pixels:
                        return False, None
                    avg_r = sum(p[0] for p in pixels) / len(pixels)
                    avg_g = sum(p[1] for p in pixels) / len(pixels)
                    avg_b = sum(p[2] for p in pixels) / len(pixels)
                    avg_color = (avg_r, avg_g, avg_b)
                    uniform_count = sum(1 for p in pixels if
                                      abs(p[0] - avg_r) <= tolerance and
                                      abs(p[1] - avg_g) <= tolerance and
                                      abs(p[2] - avg_b) <= tolerance)
                    uniformity = uniform_count / len(pixels)
                    return uniformity > 0.85, avg_color

                top_uniform, _ = is_uniform_color(top_pixels)
                bottom_uniform, _ = is_uniform_color(bottom_pixels)
                left_uniform, _ = is_uniform_color(left_pixels)
                right_uniform, _ = is_uniform_color(right_pixels)

                uniform_edges = sum([top_uniform, bottom_uniform, left_uniform, right_uniform])
                border_detected = uniform_edges >= 3
                edge_ok = not border_detected

            print(f"         {'✅' if edge_ok else '❌'} border: {'no frame' if edge_ok else f'{uniform_edges} edges uniform'}")

            # Text-area cleanliness validation - check for illustration intrusion
            # Uses tile-based local mean detection to handle gradients correctly
            with Image.open(temp_path) as img:
                rgb_img = img.convert('RGB')
                w, h = rgb_img.size

                # Get EXACT text area bounds matching PDF rendering
                roi_x, roi_y, roi_w, roi_h = get_text_area_bounds(w, h)

                # Tile-based intrusion detection (handles gradients)
                tile_grid_size = 6  # 6x6 grid of tiles
                tile_width = roi_w // tile_grid_size
                tile_height = roi_h // tile_grid_size

                # Precompute mean color for each tile
                tile_means = {}
                for tile_row in range(tile_grid_size):
                    for tile_col in range(tile_grid_size):
                        tile_x_start = roi_x + tile_col * tile_width
                        tile_y_start = roi_y + tile_row * tile_height
                        tile_x_end = min(tile_x_start + tile_width, roi_x + roi_w)
                        tile_y_end = min(tile_y_start + tile_height, roi_y + roi_h)

                        # Sample pixels in this tile
                        tile_pixels = []
                        for y in range(tile_y_start, tile_y_end):
                            for x in range(tile_x_start, tile_x_end):
                                if 0 <= x < w and 0 <= y < h:
                                    tile_pixels.append(rgb_img.getpixel((x, y)))

                        if tile_pixels:
                            r_mean = sum(p[0] for p in tile_pixels) / len(tile_pixels)
                            g_mean = sum(p[1] for p in tile_pixels) / len(tile_pixels)
                            b_mean = sum(p[2] for p in tile_pixels) / len(tile_pixels)
                            tile_means[(tile_row, tile_col)] = (r_mean, g_mean, b_mean)

                # Count intrusion pixels (compare to LOCAL tile mean, not global)
                intrusion_threshold = 40  # RGB distance threshold
                intrusion_count = 0
                total_pixels = 0

                for y in range(roi_y, roi_y + roi_h):
                    for x in range(roi_x, roi_x + roi_w):
                        if 0 <= x < w and 0 <= y < h:
                            pixel = rgb_img.getpixel((x, y))

                            # Find which tile this pixel belongs to
                            tile_col = min((x - roi_x) // tile_width, tile_grid_size - 1)
                            tile_row = min((y - roi_y) // tile_height, tile_grid_size - 1)

                            # Compare to LOCAL tile mean
                            if (tile_row, tile_col) in tile_means:
                                tile_mean = tile_means[(tile_row, tile_col)]
                                dist = ((pixel[0] - tile_mean[0]) ** 2 +
                                       (pixel[1] - tile_mean[1]) ** 2 +
                                       (pixel[2] - tile_mean[2]) ** 2) ** 0.5

                                if dist > intrusion_threshold:
                                    intrusion_count += 1

                            total_pixels += 1

                if total_pixels > 0:
                    intrusion_pct = (intrusion_count / total_pixels) * 100
                else:
                    intrusion_pct = 0

                # Threshold: text area should be mostly calm
                # Allow up to 15% intrusion (shadows, gradients are OK)
                # Above 15% = illustration is intruding into text area
                max_intrusion_pct = 15.0
                text_area_ok = intrusion_pct <= max_intrusion_pct

                print(f"         {'✅' if text_area_ok else '❌'} text_area: intrusion={intrusion_pct:.1f}% (tiles={tile_grid_size}x{tile_grid_size}, max={max_intrusion_pct}%)")

            # Pass/Fail
            qa_passed = resolution_ok and white_ok and edge_ok and text_area_ok

            if qa_passed:
                # SUCCESS
                image_path = run.images_dir / f"page_{page_num:02d}.png"
                temp_path.rename(image_path)
                print(f"      ✅ QA עבר - תמונה נשמרה")
                break
            else:
                # FAILED
                print(f"      ❌ QA נכשל")
                last_qa_failure = {
                    "white_too_high": not white_ok,
                    "border_detected": border_detected,
                    "resolution_bad": not resolution_ok,
                    "text_area_intrusion": not text_area_ok
                }

        if not image_path:
            raise RuntimeError(f"עמוד {page_num} נכשל QA אחרי {max_retries} ניסיונות")

        results.append({
            'page': page_num,
            'image_path': image_path,
            'attempts': attempts,
            'white_pct': white_pct,
            'intrusion_pct': intrusion_pct
        })

        print(f"   ✅ עמוד {page_num} הושלם ({attempts} ניסיונות)")

    print(f"\n✅ כל התמונות נוצרו ({len(results)} עמודים)")
    return results


def step4_generate_pdfs(run: RunManager, story_data: dict):
    """Stage 4: יצירת PDF לכל עמוד"""
    print("\n" + "="*80)
    print("📄 Stage 4: PDF Generation")
    print("="*80)

    pages = story_data['story']['pages']
    age = story_data['story'].get('target_age', 4)

    for page in pages:
        page_num = page['page_number']
        text = page['text']

        print(f"\n📄 עמוד {page_num}/{len(pages)}")

        # מצא תמונה
        image_path = run.images_dir / f"page_{page_num:02d}.png"
        if not image_path.exists():
            print(f"   ❌ תמונה לא נמצאה: {image_path}")
            continue

        # צור PDF בודד
        pdf_path = run.pdf_dir / f"page_{page_num:02d}.pdf"
        pdf = ProductionPDFWithNikud(str(pdf_path), target_age=age)
        pdf.add_story_page(page_num, text, image_path)
        pdf.save()

        print(f"   ✅ PDF נוצר: {pdf_path.name}")

    print(f"\n✅ כל ה-PDFs נוצרו")


def step5_validate_all(run: RunManager, story_data: dict, image_results: list):
    """Stage 5: Validation מלאה"""
    print("\n" + "="*80)
    print("🔍 Stage 5: Full Validation")
    print("="*80)

    pages = story_data['story']['pages']
    results = []

    for i, page in enumerate(pages):
        page_num = page['page_number']
        print(f"\n📄 עמוד {page_num}/{len(pages)}")

        pdf_path = run.pdf_dir / f"page_{page_num:02d}.pdf"
        image_path = run.images_dir / f"page_{page_num:02d}.png"

        if not pdf_path.exists():
            print(f"   ❌ PDF לא נמצא")
            results.append({'page': page_num, 'passed': False})
            continue

        page_result = {'page': page_num, 'passed': True}

        # בדיקה 1: Overlap
        try:
            passed, avg_diff = check_text_not_overlapping_image(pdf_path, 0, image_path)
            page_result['overlap'] = avg_diff
            page_result['overlap_ok'] = passed
            print(f"   {'✅' if passed else '❌'} Overlap: {avg_diff:.1f}")
            if not passed:
                page_result['passed'] = False
        except Exception as e:
            print(f"   ❌ Overlap check failed: {e}")
            page_result['overlap'] = None
            page_result['overlap_ok'] = False
            page_result['passed'] = False

        # בדיקה 2: Nikud
        try:
            passed, nikud_pct = check_nikud_coverage(pdf_path, 0)
            page_result['nikud_char_pct'] = nikud_pct
            page_result['nikud_ok'] = passed
            print(f"   {'✅' if passed else '❌'} Nikud: {nikud_pct:.1f}%")
            if not passed:
                page_result['passed'] = False
        except Exception as e:
            print(f"   ❌ Nikud check failed: {e}")
            page_result['nikud_char_pct'] = None
            page_result['nikud_ok'] = False
            page_result['passed'] = False

        # בדיקה 3: White
        try:
            passed, white_pct = check_image_fills_page(pdf_path, 0)
            page_result['white_pct'] = white_pct
            page_result['white_ok'] = passed
            print(f"   {'✅' if passed else '❌'} לבן: {white_pct:.1f}%")
            if not passed:
                page_result['passed'] = False
        except Exception as e:
            print(f"   ❌ White check failed: {e}")
            page_result['white_pct'] = None
            page_result['white_ok'] = False
            page_result['passed'] = False

        # הוסף attempts ו-intrusion metrics מ-Stage 3
        img_result = next((r for r in image_results if r['page'] == page_num), None)
        if img_result:
            page_result['attempts'] = img_result['attempts']
            page_result['intrusion_pct'] = img_result.get('intrusion_pct', 0)

        results.append(page_result)

    # שמור תוצאות
    report_path = run.qa_dir / "validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 דוח validation נשמר: {report_path}")

    return results


def print_final_summary(results: list):
    """מדפיס טבלה מסכמת"""
    print("\n" + "="*80)
    print("📊 דוח מסכם - 10 עמודים")
    print("="*80)

    print(f"\n{'עמוד':<6} {'לבן%':<8} {'Overlap':<10} {'Nikud%':<10} {'Intrusion%':<12} {'ניסיונות':<10} {'סטטוס':<8}")
    print("-" * 85)

    all_passed = True
    problematic_pages = []

    for r in results:
        page = r['page']
        white = f"{r.get('white_pct', 0):.1f}%" if r.get('white_pct') is not None else "N/A"
        overlap = f"{r.get('overlap', 0):.1f}" if r.get('overlap') is not None else "N/A"
        nikud = f"{r.get('nikud_char_pct', 0):.1f}%" if r.get('nikud_char_pct') is not None else "N/A"
        intrusion = f"{r.get('intrusion_pct', 0):.1f}%" if r.get('intrusion_pct') is not None else "N/A"
        attempts = r.get('attempts', 'N/A')
        status = "✅" if r['passed'] else "❌"

        print(f"{page:<6} {white:<8} {overlap:<10} {nikud:<10} {intrusion:<12} {attempts:<10} {status:<8}")

        if not r['passed']:
            all_passed = False
            problematic_pages.append(page)

    print("-" * 80)

    if all_passed:
        print("\n✅ כל העמודים עברו validation!")
    else:
        print(f"\n❌ עמודים בעייתיים: {problematic_pages}")

    # ניתוח drift
    print(f"\n📈 ניתוח Drift ויזואלי:")
    first_half = results[:5]
    second_half = results[5:]

    def avg_metric(pages, metric):
        values = [p.get(metric) for p in pages if p.get(metric) is not None]
        return sum(values) / len(values) if values else 0

    white_first = avg_metric(first_half, 'white_pct')
    white_second = avg_metric(second_half, 'white_pct')
    overlap_first = avg_metric(first_half, 'overlap')
    overlap_second = avg_metric(second_half, 'overlap')

    print(f"   לבן% - עמודים 1-5: {white_first:.1f}%, עמודים 6-10: {white_second:.1f}%")
    print(f"   Overlap - עמודים 1-5: {overlap_first:.1f}, עמודים 6-10: {overlap_second:.1f}")

    if abs(white_first - white_second) > 5:
        print(f"   ⚠️  יש drift משמעותי בלבן ({abs(white_first - white_second):.1f}%)")
    else:
        print(f"   ✅ לא זוהה drift משמעותי")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='הפקת ספר מלא - 10 עמודים')
    parser.add_argument('child_name', help='שם הילד/ה')
    parser.add_argument('age', type=int, help='גיל')
    parser.add_argument('topic', help='נושא הסיפור')
    args = parser.parse_args()

    print("="*80)
    print("📚 הפקת ספר מלא - 10 עמודים")
    print("   Stages 1-5 עם edge validation")
    print("="*80)

    # יצירת run
    run = RunManager(args.child_name, args.age, args.topic)
    print(f"\n📂 Run ID: {run.run_id}")
    print(f"📁 תיקייה: {run.base_dir}")

    try:
        # Stage 1: Story
        story_data = step1_generate_story(run, num_pages=10)

        # Stage 3: Images
        image_results = step3_generate_images(run, story_data, max_retries=3)

        # Stage 4: PDFs
        step4_generate_pdfs(run, story_data)

        # Stage 5: Validation
        validation_results = step5_validate_all(run, story_data, image_results)

        # סיכום
        print_final_summary(validation_results)

        print(f"\n✅ הפקה הושלמה!")
        print(f"📁 כל הקבצים ב: {run.base_dir}")

    except Exception as e:
        print(f"\n❌ שגיאה: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
