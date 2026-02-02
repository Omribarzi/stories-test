# Pipeline Architecture - Hebrew Children's Book Generator

## Overview

End-to-end pipeline for generating personalized Hebrew children's books with AI-generated illustrations, proper nikud (vowel marks), and production-quality PDF output. Runs in Docker.

**Input:** Child name, age, story theme
**Output:** Full illustrated book as PDF (4:3 iPad-optimized pages)

---

## Pipeline Stages

```
Stage 1: Story Generation (Claude + OpenAI quality loop)
    |
Stage 3: Image Generation (Gemini 2.5 Flash Image + QA loop)
    |
Stage 4: PDF Generation (Pillow/libraqm + ReportLab)
    |
Stage 5: Validation (overlap, nikud coverage, white fill)
```

> Stage 2 was removed (originally character design). Numbering kept for backward compatibility.

---

## Key Challenges & Decisions

### 1. Hebrew Nikud (Vowel Marks) Rendering

**Challenge:** ReportLab cannot render nikud correctly. Hebrew combining marks (U+05B0-U+05BD) require OpenType GPOS mark-to-base positioning, which ReportLab's text engine doesn't support. Nikud appears displaced, floating above or beside letters.

**Failed approaches:**
- **ReportLab native text** - Nikud detached from letters, unusable
- **Manual letter-by-letter positioning** (`HebrewNikudRenderer`) - Built a per-letter offset table mapping each Hebrew letter to its nikud x/y offset. Worked for common cases but failed for rare letters, double-nikud (dagesh + vowel), and varied font metrics
- **uharfbuzz direct** - Correct shaping but complex integration with PDF canvas

**Solution: Pillow + libraqm (HarfBuzz + fribidi)**
- Each text line rendered to a transparent RGBA PNG image using Pillow's text engine
- When Pillow is compiled with `libraqm-dev`, it delegates shaping to HarfBuzz (GPOS) and bidi to fribidi
- The PNG image is then placed in the PDF via `drawImage(mask='auto')`
- This gives pixel-perfect nikud at the cost of non-selectable text in the PDF

**Key parameter: `_render_scale = 4`**
- Text rendered at 4x target size, then scaled down in PDF
- At 2x, thin nikud marks (chirik, shva - only ~4px wide) disappeared after downscaling
- 4x ensures all marks are crisp. Tradeoff: larger file size (~2MB/page vs ~0.5MB)

### 2. Font Selection

**Challenge:** Need a single font with Hebrew letters + nikud marks + Latin punctuation (. ! ? " ,).

**Failed approaches:**
- **NotoSansHebrew** - Has Hebrew + nikud but NO Latin glyphs. Punctuation rendered as square boxes (tofu)
- **Dual-font rendering** - Split text into Hebrew/punctuation runs, render each with different font, composite. Broke HarfBuzz shaping context across word boundaries, causing missing nikud
- **Mixed canvas** - Hebrew words as Pillow images + punctuation via ReportLab drawString. Per-word images lost quality; visual mismatch between rendering engines

**Solution: Rubik font from Google Fonts**
- Single TTF file with Hebrew, nikud marks, AND Latin punctuation
- Downloaded from Google Fonts gstatic CDN (not GitHub - GitHub redirects to HTML)
- Bundled at `assets/fonts/Rubik-Regular.ttf` (170KB)

### 3. Consistent Font Size Across Pages

**Challenge:** Font size was calculated per-page based on word count. Pages with slightly fewer words got larger font, creating visual inconsistency.

**Solution: `set_fixed_font_size()`**
- Calculate once based on the longest page text
- All pages use the same font size
- Called before page generation in both `generate_3pages.py` and `run_full_book_10pages.py`

### 4. Docker Build with libraqm

**Challenge:** Pillow's pip wheel is pre-compiled without libraqm support. Need to compile from source.

**Solution:**
```dockerfile
RUN apt-get install -y libraqm-dev libfreetype6-dev libfribidi-dev libharfbuzz-dev
RUN pip install --no-binary Pillow Pillow
```
- `--no-binary Pillow` forces compilation from source
- At build time, Pillow detects libraqm headers and enables raqm support
- Runtime check: `features.check('raqm')` returns True

### 5. Nikud Text Generation

**Challenge:** Raw Hebrew text from the story generator has no nikud. Need to add vowel marks to every word.

**Approach:**
1. Manual dictionary (~250 common words) applied first - zero API cost
2. Claude API (`claude-sonnet-4-5-20250514`) for remaining words - full nikud with linguistic context
3. Without API key, only dictionary words get nikud (partial coverage)

**Docker requirement:** Must pass `--env-file .env` to give the container access to `ANTHROPIC_API_KEY`.

### 6. Image QA Loop

**Challenge:** AI-generated images often have issues: borders/frames, too much white space, illustration bleeding into the text area.

**Solution: 4-check QA loop with delta prompts (max 3 retries)**
1. **Resolution** - Must maintain 4:3 aspect ratio (+-5%)
2. **White threshold** - Max 21% white pixels (numpy vectorized)
3. **Border detection** - Edge uniformity check on 4 edges (fails if 3+ uniform)
4. **Text-area intrusion** - Tile-based local mean detection (6x6 grid). Compares each pixel to its local tile mean, not global. This correctly handles gradients while detecting illustration intrusion. Max 15%.

Each failed check adds a "delta prompt" to the next retry, e.g.:
- White too high -> "Add subtle warm textures"
- Border detected -> "Full-bleed illustration extending to ALL edges"
- Text area intrusion -> "Push all characters/objects LEFT"

### 7. Story Quality Loop

**Challenge:** AI-generated stories often have issues: too preachy, passive characters, age-inappropriate sentence length.

**Solution: Multi-gate quality loop**
1. **Best-of-2** - First iteration generates 2 drafts, picks better one
2. **Pre-score gate** (deterministic, zero API calls):
   - Banned phrases detection ("הוא צפה בשקט", "המוסר של הסיפור")
   - Sentence length validation per age
   - Preachy language detection
   - Ending must have punctuation
3. **OpenAI evaluation** - Median-of-3 scoring (8 weighted criteria, target >= 90/100)
4. **Edit mode** - If score too low, Claude gets feedback + existing story for targeted edits
5. **Hebrew quality check** - Grammar fixes, tense consistency, age-appropriate vocabulary

---

## File Structure

```
services/pipeline/
├── run_full_book_10pages.py    # Main entry point - full pipeline (Stages 1-5)
├── generate_3pages.py          # Quick 3-page test with illustrations
├── test_text_only.py           # Text rendering test (no images)
├── Dockerfile                  # Docker build with libraqm
├── requirements.txt            # Python dependencies
├── .dockerignore               # Excludes .env, output, media
├── .gitignore                  # Excludes generated files
├── assets/
│   └── fonts/
│       ├── Rubik-Regular.ttf           # Primary font (Hebrew+Latin+nikud)
│       ├── NotoSansHebrew-Regular.ttf  # Fallback (Hebrew only)
│       └── NotoSans-Regular.ttf        # Latin fallback
├── config/
│   ├── production_config.json  # Pipeline configuration
│   └── rating_criteria.json    # Story evaluation criteria
└── src/
    ├── hebrew_text_renderer.py       # Core: Pillow+libraqm text-to-image
    ├── production_pdf_with_nikud.py  # PDF generator with nikud
    ├── hebrew_text_processor.py      # Nikud generation (dictionary + Claude API)
    ├── hebrew_text_quality_checker.py # Hebrew grammar/style checker
    ├── image_generator.py            # AI image generation (Gemini/DALL-E/Stability)
    ├── claude_agent.py               # Claude API wrapper for story generation
    ├── openai_agent.py               # OpenAI API wrapper for evaluation
    ├── story_style_guidelines.py     # Age matrix, style validation
    ├── rating_system.py              # Story rating criteria
    ├── validate_single_page.py       # Page validation (overlap, nikud, white)
    ├── professional_cover_layout.py  # Cover page layout
    ├── hebrew_nikud_renderer.py      # Legacy: manual nikud positioning (cover only)
    └── model_config.py               # Model selection config
```

---

## Running

### Docker (recommended)

```bash
# Build
docker build -t stories-pipeline services/pipeline/

# Run full book
docker run --rm --env-file services/pipeline/.env \
  -v "$(pwd)/services/pipeline/data:/app/data" \
  stories-pipeline python3 run_full_book_10pages.py "איתי" 6 "כעסים שיוצאים מהידיים"

# Run 3-page test
docker run --rm --env-file services/pipeline/.env \
  -v "$(pwd)/services/pipeline/output_3pages:/app/output_3pages" \
  stories-pipeline python3 generate_3pages.py
```

### Required Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...    # Story generation + nikud
OPENAI_API_KEY=sk-...           # Story evaluation
GOOGLE_API_KEY=AI...            # Image generation (Gemini)
```

### Pages by Age

| Age | Pages | Words/Page | Max Words/Sentence | Font Base |
|-----|-------|------------|--------------------|-----------|
| 2   | 8     | 15-25      | 8                  | 24pt      |
| 3   | 13    | 20-35      | 10                 | 24pt      |
| 4   | 14    | 25-40      | 10                 | 24pt      |
| 5   | 16    | 30-50      | 12                 | 22pt      |
| 6   | 17    | 40-60      | 14                 | 22pt      |
| 7   | 19    | 40-60      | 14                 | 20pt      |
| 8   | 19    | 40-60      | 14                 | 20pt      |

---

## Cost Estimate (per book)

| Service | Usage | ~Cost |
|---------|-------|-------|
| Claude (story + nikud) | ~20K tokens | $0.40 |
| OpenAI (evaluation) | 3 runs GPT-4o-mini | $0.02 |
| Gemini (images) | 17-22 images | $0.05 |
| **Total** | | **~$0.50** |

---

## Known Limitations

1. **Text not selectable in PDF** - Because text is rendered as images via Pillow
2. **Nikud validation false negatives** - PyMuPDF text extraction can't detect nikud in image-rendered text, so Stage 5 nikud check always reports 0%
3. **Image generation non-deterministic** - Same prompt can produce different results; QA loop mitigates but doesn't guarantee visual consistency across pages
4. **Cover page uses legacy nikud renderer** - `ProfessionalCoverLayout` still uses `HebrewNikudRenderer` (manual offsets) instead of `HebrewTextRenderer` (Pillow+libraqm)
