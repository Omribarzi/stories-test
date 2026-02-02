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
import re
import hashlib
import time
from datetime import datetime
from PIL import Image
import numpy as np

from claude_agent import ClaudeAgent
from openai_agent import OpenAIAgent
from hebrew_text_quality_checker import HebrewTextQualityChecker
from story_style_guidelines import validate_story_not_preachy, get_age_params
from image_generator import ImageGenerator
from production_pdf_with_nikud import ProductionPDFWithNikud
from validate_single_page import (
    check_image_fills_page,
    check_nikud_coverage,
    check_text_not_overlapping_image
)

# =====================================================================
# Quality Loop Configuration
# =====================================================================
QUALITY_LOOP_ENABLED = True
MIN_SCORE = 90
MAX_ITERATIONS = 3
COST_MODE = "balanced"       # "fast", "balanced", "premium"
MAX_EVAL_CALLS = 3           # max OpenAI evaluation calls per story
MAX_TOTAL_SECONDS = 600      # time budget for the quality loop
FALLBACK_POLICY = "accept_best"  # "accept_best", "rerun_story", "stop"

# COST_MODE presets (override defaults above when applied)
COST_MODE_PRESETS = {
    "fast":     {"max_iterations": 2, "min_score": 88, "max_total_seconds": 420, "openai_model": "gpt-4o-mini"},
    "balanced": {"max_iterations": 3, "min_score": 90, "max_total_seconds": 600, "openai_model": "gpt-4o-mini"},
    "premium":  {"max_iterations": 5, "min_score": 92, "max_total_seconds": 900, "openai_model": "gpt-4o"},
}


# =====================================================================
# Pre-score quality gate — deterministic, zero API calls
# =====================================================================
BANNED_PHRASES = [
    "הוא צפה בשקט",       # silent observing adult
    "היא צפתה בשקט",
    "צפו בשקט",
    "עמד בצד וחייך",
    "עמדה בצד וחייכה",
    "המוסר של הסיפור",    # preachy closing
    "ולמדו שיעור חשוב",
    "והמסר הוא",
]


def _pre_score_gate(story: dict, age: int = 5) -> dict:
    """
    Deterministic quality gate run BEFORE any OpenAI eval.
    Returns {pass: bool, reasons: [...], metrics: {...}}.
    max_words_per_sentence is derived from the age matrix.
    """
    age_p = get_age_params(age)
    max_sentence_words = age_p["max_words_per_sentence"]

    pages = story.get("pages", [])
    reasons = []

    # --- metric: max sentence word count ---
    max_words = 0
    long_sentences = []
    for page in pages:
        text = page.get("text", "")
        sentences = re.split(r'[.!?।]', text)
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            word_count = len(s.split())
            if word_count > max_words:
                max_words = word_count
            if word_count > max_sentence_words:
                long_sentences.append((page["page_number"], word_count, s[:60]))

    if long_sentences:
        pages_str = ", ".join(f"p{p}({w}w)" for p, w, _ in long_sentences[:3])
        reasons.append(f"long_sentences: {pages_str}")

    # --- metric: banned phrases ---
    banned_hits = []
    for page in pages:
        text = page.get("text", "")
        for phrase in BANNED_PHRASES:
            if phrase in text:
                banned_hits.append((page["page_number"], phrase))
    if banned_hits:
        hits_str = ", ".join(f"p{p}:'{ph}'" for p, ph in banned_hits[:3])
        reasons.append(f"banned_phrases: {hits_str}")

    # --- metric: preachy phrases (from story_style_guidelines) ---
    full_text = " ".join(page.get("text", "") for page in pages)
    preachy_warnings = validate_story_not_preachy(full_text)
    if preachy_warnings:
        preachy_str = ", ".join(w.split("'")[1] for w in preachy_warnings[:3] if "'" in w)
        reasons.append(f"preachy_phrases: {preachy_str}")

    # --- metric: ending closure ---
    ending_present = False
    if pages:
        last_text = pages[-1].get("text", "").strip()
        # Must end with sentence-ending punctuation
        if last_text and last_text[-1] in '.!?"':
            ending_present = True
    if not ending_present:
        reasons.append("no_closure: last page missing sentence-ending punctuation")

    passed = len(reasons) == 0
    return {
        "pass": passed,
        "reasons": reasons,
        "metrics": {
            "max_sentence_words": max_words,
            "banned_hits": len(banned_hits),
            "preachy_hits": len(preachy_warnings),
            "ending_present": ending_present,
        },
    }


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


def _generate_story_once(agent: ClaudeAgent, run: RunManager, num_pages: int,
                         existing_feedback: str = None,
                         existing_story: dict = None) -> dict:
    """
    Single story generation call using ClaudeAgent.create_story().
    Wraps the existing mechanism with run-specific parameters.

    When existing_feedback + existing_story are provided, Claude will EDIT
    the existing story rather than writing from scratch.
    """
    # Build structured topic/character/style dicts that ClaudeAgent.create_story() expects
    topic = {
        "name": run.topic,
        "sub_topics": [run.topic],
        "educational_value": run.topic,
    }
    character = {
        "name": run.child_name,
        "description": f"ילד/ה בגיל {run.age}",
    }
    style_guide = {
        "tone": "חם ומעודד",
        "words_per_page": "40-60",
        "visual_style": "איורים צבעוניים מודרניים לספרי ילדים",
    }

    # Use ClaudeAgent.create_story() — the existing mechanism
    story = agent.create_story(
        topic=topic,
        character=character,
        style_guide=style_guide,
        existing_feedback=existing_feedback,
        existing_story=existing_story,
        age=run.age,
        num_pages=num_pages,
    )

    # Wrap in the expected structure and ensure target_age
    if "story" not in story:
        # ClaudeAgent.create_story() returns the story dict directly (title, pages, ...)
        story_data = {"story": story}
    else:
        story_data = story

    story_data["story"]["target_age"] = run.age

    # Trim/pad pages
    actual_pages = len(story_data["story"]["pages"])
    if actual_pages != num_pages:
        print(f"   ⚠️  נוצרו {actual_pages} עמודים במקום {num_pages}, קוצץ")
        if actual_pages > num_pages:
            story_data["story"]["pages"] = story_data["story"]["pages"][:num_pages]

    return story_data


def step1_generate_story(run: RunManager, num_pages: int = 10):
    """
    Stage 1: Story Generation with Quality Loop

    Uses existing mechanisms:
    - ClaudeAgent.create_story() for writing
    - OpenAIAgent.rate_story() for evaluation
    - HebrewTextQualityChecker.check_full_story() for Hebrew QA

    Controlled by module-level QUALITY_LOOP_ENABLED, COST_MODE, etc.
    """
    print("\n" + "="*80)
    print(f"📖 Stage 1: Story Generation - {num_pages} עמודים")
    print("="*80)

    agent = ClaudeAgent()

    # -------------------------------------------------------
    # If quality loop is disabled, generate once and return
    # -------------------------------------------------------
    if not QUALITY_LOOP_ENABLED:
        print("   ℹ️  Quality loop disabled — single generation")
        story_data = _generate_story_once(agent, run, num_pages)
        story_path = run.save_story(story_data)
        title = story_data["story"]["title"]
        print(f"\n✅ סיפור נוצר: {title}")
        print(f"   עמודים: {len(story_data['story']['pages'])}")
        print(f"   💾 נשמר: {story_path}")
        return story_data

    # -------------------------------------------------------
    # Quality loop — ping-pong between Claude and OpenAI
    # Uses: OpenAIAgent.rate_story(), RatingSystem (existing)
    # -------------------------------------------------------
    preset = COST_MODE_PRESETS.get(COST_MODE, COST_MODE_PRESETS["balanced"])
    max_iter = min(MAX_ITERATIONS, preset["max_iterations"])
    min_score = max(MIN_SCORE, preset["min_score"])
    eval_model = preset["openai_model"]
    time_budget = preset.get("max_total_seconds", MAX_TOTAL_SECONDS)

    print(f"\n   🎛️  Quality Loop Configuration:")
    print(f"      COST_MODE:        {COST_MODE}")
    print(f"      max_iterations:   {max_iter}")
    print(f"      min_score:        {min_score}")
    print(f"      eval_model:       {eval_model}")
    print(f"      MAX_EVAL_CALLS:   {MAX_EVAL_CALLS}")
    print(f"      time_budget:      {time_budget}s")
    print(f"      FALLBACK_POLICY:  {FALLBACK_POLICY}")

    openai_agent = OpenAIAgent(model=eval_model)

    # Build topic dict for OpenAIAgent.rate_story()
    topic_for_rating = {
        "name": run.topic,
        "educational_value": run.topic,
    }

    loop_start = time.time()
    eval_calls = 0
    best_story = None
    best_score = 0
    feedback = None
    rerun_attempted = False

    for iteration in range(1, max_iter + 1):
        iter_start = time.time()
        elapsed_total = iter_start - loop_start

        # Budget checks
        if elapsed_total > time_budget:
            print(f"\n   ⏱️  Time budget exceeded ({elapsed_total:.0f}s > {time_budget}s)")
            break
        if eval_calls >= MAX_EVAL_CALLS:
            print(f"\n   💰 Eval call budget exceeded ({eval_calls} >= {MAX_EVAL_CALLS})")
            break

        print(f"\n   --- iteration {iteration}/{max_iter} ---")

        # =============================================================
        # 1. Generate story (best-of-2 on first draft, single on edits)
        # =============================================================
        if iteration == 1 and not feedback:
            # Best-of-2: generate two drafts, pick better by gate metrics
            print(f"      [BEST_OF_2] generating 2 drafts...")
            t_claude = time.time()
            drafts = []
            for d in range(2):
                try:
                    draft = _generate_story_once(agent, run, num_pages)
                    drafts.append(draft)
                    print(f"      [BEST_OF_2] draft {chr(65+d)}: {len(draft['story']['pages'])} pages generated")
                except Exception as e:
                    print(f"      [BEST_OF_2] draft {chr(65+d)}: FAILED ({e})")

            if not drafts:
                print(f"      [BEST_OF_2] result: ABORT — both drafts failed")
                continue

            # Pick best by gate: prefer passing, then lower max_sentence_words
            gate_results = [(d, _pre_score_gate(d["story"], age=run.age)) for d in drafts]
            for idx, (_, g) in enumerate(gate_results):
                m = g["metrics"]
                print(f"      [BEST_OF_2] draft {chr(65+idx)}: gate={'PASS' if g['pass'] else 'FAIL'}, max_sentence_words={m['max_sentence_words']}, banned_hits={m['banned_hits']}, ending_present={m['ending_present']}")
                if not g["pass"]:
                    for r in g["reasons"]:
                        print(f"      [BEST_OF_2]   reason: {r}")

            # Sort: passing first, then by max_sentence_words ascending
            gate_results.sort(key=lambda x: (not x[1]["pass"], x[1]["metrics"]["max_sentence_words"]))
            story_data = gate_results[0][0]
            picked_gate = gate_results[0][1]
            picked_label = chr(65 + drafts.index(story_data))
            claude_time = time.time() - t_claude
            print(f"      [BEST_OF_2] selected: draft {picked_label} (gate={'PASS' if picked_gate['pass'] else 'FAIL'}, max_words={picked_gate['metrics']['max_sentence_words']})")
            print(f"      [BEST_OF_2] generation time: {claude_time:.1f}s")
        else:
            # Single generation (edit mode if we have feedback)
            if feedback and best_story:
                print(f"      [EDIT_MODE] Claude editing story (targeted fix)...")
                print(f"      [EDIT_MODE] feedback snippet: {feedback[:150]}...")
            else:
                print(f"      📝 Claude writing story (fresh draft)...")
            t_claude = time.time()
            try:
                story_data = _generate_story_once(
                    agent, run, num_pages,
                    existing_feedback=feedback,
                    existing_story=best_story["story"] if (feedback and best_story) else None,
                )
            except Exception as e:
                print(f"      ❌ Story generation failed: {e}")
                continue
            claude_time = time.time() - t_claude
            if feedback and best_story:
                print(f"      [EDIT_MODE] generation time: {claude_time:.1f}s")
            else:
                print(f"      [claude] generation time: {claude_time:.1f}s")

        # =============================================================
        # 2. Pre-score gate — deterministic, zero API calls
        # =============================================================
        gate = _pre_score_gate(story_data["story"], age=run.age)
        m = gate["metrics"]
        print(f"      [PRE_SCORE_GATE] iteration={iteration} result={'PASS' if gate['pass'] else 'FAIL'} | max_sentence_words={m['max_sentence_words']}, banned_hits={m['banned_hits']}, preachy_hits={m['preachy_hits']}, ending_present={m['ending_present']}")

        if not gate["pass"]:
            # FAIL: skip eval, go directly to edit with gate feedback
            print(f"      [PRE_SCORE_GATE] FAIL reasons ({len(gate['reasons'])}):")
            for r in gate["reasons"]:
                print(f"      [PRE_SCORE_GATE]   - {r}")
            # Log offending sentences if long_sentences triggered
            age_limit = get_age_params(run.age)["max_words_per_sentence"]
            for page in story_data["story"].get("pages", []):
                for s in re.split(r'[.!?।]', page.get("text", "")):
                    s = s.strip()
                    if s and len(s.split()) > age_limit:
                        print(f"      [PRE_SCORE_GATE]   offending p{page['page_number']}({len(s.split())}w): \"{s[:80]}\"")
            print(f"      [PRE_SCORE_GATE] action: skip eval → send to EDIT_MODE")

            gate_feedback = "בעיות שנמצאו בבדיקה אוטומטית (תקן רק אותן):\n"
            for r in gate["reasons"]:
                gate_feedback += f"- {r}\n"
            feedback = gate_feedback
            # Still track as best if we have nothing better
            if best_story is None:
                best_story = story_data
            continue

        # =============================================================
        # 3. OpenAI evaluates (median-of-3 via rate_story)
        # =============================================================
        print(f"      [MEDIAN_EVAL] starting (model={eval_model}, runs=3)...")
        eval_calls += 1

        try:
            evaluation = openai_agent.rate_story(story_data["story"], topic_for_rating, age=run.age)
            score = evaluation["rating"]["weighted_score"]
        except Exception as e:
            print(f"      ❌ Evaluation failed: {e}")
            if best_story is None:
                best_story = story_data
            continue

        iter_elapsed = time.time() - iter_start
        total_elapsed = time.time() - loop_start

        # Track best
        if score > best_score:
            best_score = score
            best_story = story_data

        # Log
        print(f"      📊 Score:            {score}/100 (target: {min_score})")
        print(f"      🕐 Iteration time:   {iter_elapsed:.1f}s")
        print(f"      🕐 Cumulative time:  {total_elapsed:.1f}s")
        print(f"      💰 OpenAI eval calls: {eval_calls}/{MAX_EVAL_CALLS}")
        print(f"      🏆 Best score so far: {best_score}/100")

        # Check if approved
        if score >= min_score:
            print(f"      ✅ Story approved! (score {score} >= {min_score})")
            break
        else:
            # Extract feedback for next iteration
            feedback = evaluation["rating"].get("suggestions", "")
            print(f"      ❌ Below threshold (score {score} < {min_score})")
            if feedback:
                print(f"      💡 Feedback: {feedback[:200]}...")

    # -------------------------------------------------------
    # Fallback policy if not approved
    # -------------------------------------------------------
    if best_score < min_score:
        total_elapsed = time.time() - loop_start
        print(f"\n   ⚠️  Quality loop ended without approval")
        print(f"      Best score: {best_score}/100 (target: {min_score})")
        print(f"      Total time: {total_elapsed:.1f}s, Eval calls: {eval_calls}")
        print(f"      Fallback policy: {FALLBACK_POLICY}")

        if FALLBACK_POLICY == "accept_best":
            print(f"      → Accepting best version (score {best_score})")
        elif FALLBACK_POLICY == "rerun_story" and not rerun_attempted:
            print(f"      → Rerunning story generation (one attempt)")
            rerun_attempted = True
            try:
                story_data = _generate_story_once(agent, run, num_pages)
                best_story = story_data
                print(f"      → Rerun complete")
            except Exception as e:
                print(f"      → Rerun failed: {e}")
        elif FALLBACK_POLICY == "stop":
            raise RuntimeError(
                f"Quality gate failed: best score {best_score} < {min_score} "
                f"after {eval_calls} evaluations in {total_elapsed:.1f}s"
            )

    story_data = best_story

    # -------------------------------------------------------
    # Hebrew text quality gate (existing: HebrewTextQualityChecker)
    # -------------------------------------------------------
    print(f"\n   🔤 Hebrew Text Quality Check...")
    try:
        checker = HebrewTextQualityChecker()
        check_result = checker.check_full_story(story_data)
        pages_changed = check_result["pages_changed"]
        total_edits = check_result["total_edits"]
        blockers = check_result["blockers_remaining"]

        print(f"      Pages changed: {pages_changed}")
        print(f"      Total edits:   {total_edits}")
        print(f"      Blockers:      {blockers}")

        if blockers > 0:
            print(f"      ⚠️  {blockers} blockers remain — applying fallback")
            if FALLBACK_POLICY == "stop":
                raise RuntimeError(f"Hebrew quality check: {blockers} blockers remaining")
            # accept_best / rerun_story: continue with improved version
        story_data = check_result["improved_story"]
    except RuntimeError:
        raise
    except Exception as e:
        print(f"      ⚠️  Hebrew quality check failed: {e}")
        print(f"      → Continuing with current story")

    # -------------------------------------------------------
    # Save and return
    # -------------------------------------------------------
    story_path = run.save_story(story_data)

    title = story_data["story"]["title"]
    total_elapsed = time.time() - loop_start
    print(f"\n✅ סיפור נוצר: {title}")
    print(f"   עמודים:     {len(story_data['story']['pages'])}")
    print(f"   ציון סופי:  {best_score}/100")
    print(f"   קריאות eval: {eval_calls}")
    print(f"   זמן כולל:   {total_elapsed:.1f}s")
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

            # White percentage (numpy for speed)
            with Image.open(temp_path) as img:
                arr = np.array(img.convert('RGB'))
                white_mask = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240)
                white_pct = (white_mask.sum() / white_mask.size) * 100
            white_ok = white_pct <= 21.0
            print(f"         {'✅' if white_ok else '❌'} לבן: {white_pct:.1f}%")

            # Edge border detection (numpy for speed)
            with Image.open(temp_path) as img:
                arr = np.array(img.convert('RGB'))
                h, w = arr.shape[:2]
                edge_t = 5

                def is_uniform_edge(edge_arr, tolerance=30):
                    if edge_arr.size == 0:
                        return False
                    pixels = edge_arr.reshape(-1, 3).astype(np.float32)
                    avg = pixels.mean(axis=0)
                    within = np.all(np.abs(pixels - avg) <= tolerance, axis=1)
                    return (within.sum() / len(within)) > 0.85

                top_uniform = is_uniform_edge(arr[:edge_t, :, :])
                bottom_uniform = is_uniform_edge(arr[-edge_t:, :, :])
                left_uniform = is_uniform_edge(arr[:, :edge_t, :])
                right_uniform = is_uniform_edge(arr[:, -edge_t:, :])

                uniform_edges = sum([top_uniform, bottom_uniform, left_uniform, right_uniform])
                border_detected = uniform_edges >= 3
                edge_ok = not border_detected

            print(f"         {'✅' if edge_ok else '❌'} border: {'no frame' if edge_ok else f'{uniform_edges} edges uniform'}")

            # Text-area cleanliness validation (numpy, tile-based local mean)
            with Image.open(temp_path) as img:
                arr = np.array(img.convert('RGB')).astype(np.float32)
                h_img, w_img = arr.shape[:2]

                roi_x, roi_y, roi_w, roi_h = get_text_area_bounds(w_img, h_img)

                # Extract ROI
                y_end = min(roi_y + roi_h, h_img)
                x_end = min(roi_x + roi_w, w_img)
                roi = arr[roi_y:y_end, roi_x:x_end, :]

                # Tile-based intrusion detection (6x6 grid)
                tile_grid_size = 6
                rh, rw = roi.shape[:2]

                if rh > 0 and rw > 0:
                    # Compute per-tile mean and broadcast back to pixel level
                    th = max(1, rh // tile_grid_size)
                    tw = max(1, rw // tile_grid_size)
                    # Pad roi to be evenly divisible
                    pad_h = (tile_grid_size - rh % tile_grid_size) % tile_grid_size
                    pad_w = (tile_grid_size - rw % tile_grid_size) % tile_grid_size
                    roi_padded = np.pad(roi, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
                    ph, pw = roi_padded.shape[:2]
                    th2, tw2 = ph // tile_grid_size, pw // tile_grid_size
                    # Reshape into tiles, compute mean per tile
                    tiles = roi_padded.reshape(tile_grid_size, th2, tile_grid_size, tw2, 3)
                    tile_means = tiles.mean(axis=(1, 3))  # shape: (6, 6, 3)
                    # Expand back to pixel level
                    local_means = tile_means.repeat(th2, axis=0).repeat(tw2, axis=1)[:rh, :rw, :]
                    # Euclidean distance from local mean
                    dist = np.sqrt(((roi - local_means) ** 2).sum(axis=2))
                    intrusion_count = (dist > 40).sum()
                    total_pixels = rh * rw
                    intrusion_pct = (intrusion_count / total_pixels) * 100
                else:
                    intrusion_pct = 0

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
            # Use best attempt instead of failing entirely
            print(f"      ⚠️  עמוד {page_num} נכשל QA אחרי {max_retries} ניסיונות — משתמש בניסיון האחרון")
            best_attempt = run.images_dir / f"page_{page_num:02d}_attempt{max_retries}.png"
            if best_attempt.exists():
                image_path = run.images_dir / f"page_{page_num:02d}.png"
                best_attempt.rename(image_path)

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
    """Stage 4: יצירת PDF — ספר אחד מאוחד + PDFs בודדים"""
    print("\n" + "="*80)
    print("📄 Stage 4: PDF Generation")
    print("="*80)

    pages = story_data['story']['pages']
    age = story_data['story'].get('target_age', 4)

    # ספר מאוחד — כל העמודים ב-PDF אחד
    combined_path = run.pdf_dir / "book.pdf"
    combined_pdf = ProductionPDFWithNikud(str(combined_path), target_age=age)
    combined_pdf.set_fixed_font_size([p['text'] for p in pages])

    for page in pages:
        page_num = page['page_number']
        text = page['text']

        print(f"\n📄 עמוד {page_num}/{len(pages)}")

        # מצא תמונה
        image_path = run.images_dir / f"page_{page_num:02d}.png"
        if not image_path.exists():
            print(f"   ❌ תמונה לא נמצאה: {image_path}")
            continue

        # הוסף לספר המאוחד
        combined_pdf.add_story_page(page_num, text, image_path)

        # צור גם PDF בודד (ל-validation)
        pdf_path = run.pdf_dir / f"page_{page_num:02d}.pdf"
        single_pdf = ProductionPDFWithNikud(str(pdf_path), target_age=age)
        single_pdf._fixed_font_size = combined_pdf._fixed_font_size
        single_pdf.add_story_page(page_num, text, image_path)
        single_pdf.save()

        print(f"   ✅ PDF נוצר: {pdf_path.name}")

    combined_pdf.save()
    print(f"\n✅ כל ה-PDFs נוצרו")
    print(f"📚 ספר מאוחד: {combined_path}")


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
    parser.add_argument('--pages', type=int, default=None, help='מספר עמודים (ברירת מחדל: לפי גיל)')
    args = parser.parse_args()

    # Resolve num_pages from age matrix if not explicitly set
    age_params = get_age_params(args.age)
    num_pages = args.pages if args.pages is not None else age_params["pages"]

    print("="*80)
    print(f"📚 הפקת ספר מלא - {num_pages} עמודים (גיל {args.age})")
    print("   Stages 1-5 עם edge validation")
    print("="*80)

    # יצירת run
    run = RunManager(args.child_name, args.age, args.topic)
    print(f"\n📂 Run ID: {run.run_id}")
    print(f"📁 תיקייה: {run.base_dir}")

    try:
        # Stage 1: Story
        story_data = step1_generate_story(run, num_pages=num_pages)

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
