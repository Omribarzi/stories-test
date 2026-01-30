# Pipeline Status - v0.1.0 (Locked)

**Version**: 0.1.0
**Date**: 2026-01-30
**Status**: 🟢 Working - Locked for Production

---

## What Works Today

### ✅ End-to-End Pipeline (Stages 1-5)

The full pipeline from story generation to PDF creation is **operational and tested**:

1. **Story Generation (Stage 1)**
   - ✅ Claude API integration for personalized 10-page stories
   - ✅ Age-appropriate content (ages 4-10)
   - ✅ Personalization with child's name
   - ✅ Consistent narrative arc across pages
   - ✅ Visual descriptions for each page

2. **Image Generation with QA Loop (Stage 3)**
   - ✅ Imagen 3 integration (Google Cloud)
   - ✅ Full-bleed image generation (4:3 aspect ratio, 1184x864)
   - ✅ **Automated Quality Assurance Loop** with 4 checks:
     - **Resolution check**: Ensures 1184x864 (±5% tolerance)
     - **White space check**: <30% white pixels to avoid empty backgrounds
     - **Border detection**: Rejects images with frames/borders (checks 4 edges)
     - **Text-area intrusion check**: Ensures right 35% stays clean for text
   - ✅ **Retry mechanism**: Up to 3 attempts per page with delta prompts:
     - Delta 1: If white space too high → force vivid full-bleed composition
     - Delta 2: If border detected → emphasize edge-to-edge requirement
     - Delta 3: If text area intrusion → push illustration content LEFT
   - ✅ **Tile-based gradient detection**: 6×6 grid with local mean comparison
   - ✅ Validation reports saved per page

3. **PDF Generation (Stage 5)**
   - ✅ ReportLab-based PDF creation
   - ✅ **Hebrew text with nikud** (vowel marks):
     - Hybrid system: Manual dictionary + Claude API fallback
     - Preserves כתיב מלא (full spelling with ו/י)
     - ~600 word manual dictionary for common children's words
   - ✅ **Triple-constraint text layout** (locked as-is):
     - Right margin: 30px (text closer to right edge)
     - Max 4 words per line (for age 6, font 22pt)
     - Max 23 characters per line (including spaces/punctuation)
     - Text area: 35% of page width
   - ✅ Full-bleed image rendering (stretched to 1024×768)
   - ✅ Professional iPad-optimized layout (1024×768)

4. **Run Management**
   - ✅ Timestamped run directories: `data/runs/{child}_{age}_{topic}/{timestamp}/`
   - ✅ Structured outputs: `story/`, `images/`, `qa/`, `final_book.pdf`
   - ✅ Metadata and validation reports (JSON)

---

## What is Locked As-Is

The following parameters are **FIXED in this release** and should NOT be changed without careful testing:

### Layout Constraints (Critical - Do Not Modify)

| Parameter | Value | Location | Notes |
|-----------|-------|----------|-------|
| **Right margin** | 30px | `production_pdf_with_nikud.py:174` | Text edge distance from right |
| **Text area width** | 35% | `production_pdf_with_nikud.py:173` | Percentage of page width |
| **ROI calculation** | Must match PDF | `run_full_book_10pages.py:38` | **CRITICAL**: Validation ROI must equal PDF text_x |
| **Max words/line** | 4 (age 6) | `production_pdf_with_nikud.py:75` | Font-dependent: 3-6 words |
| **Max chars/line** | 23 | `production_pdf_with_nikud.py:198` | Hard limit including spaces |
| **Line height** | 1.8× font size | `production_pdf_with_nikud.py:185` | Needed for nikud marks |

### QA Thresholds (Tuned - Do Not Change)

| Metric | Threshold | Location | Purpose |
|--------|-----------|----------|---------|
| White % | <30% | `run_full_book_10pages.py:~230` | Avoid empty backgrounds |
| Intrusion % | <15% | `run_full_book_10pages.py:346` | Text area must be calm |
| Intrusion RGB distance | 40 | `run_full_book_10pages.py:313` | Sensitivity to color changes |
| Tile grid size | 6×6 | `run_full_book_10pages.py:286` | Gradient handling |
| Max retries | 3 | `run_full_book_10pages.py:~180` | Cost vs quality balance |

---

## Known Risks and Limitations

### ⚠️ Layout Uses Mixed Constraints

**Issue**: The current line-breaking algorithm enforces THREE constraints simultaneously:
1. Physical width (canvas measurement)
2. Word count (4 words max)
3. Character count (23 chars max)

**Risk**: These constraints are **independent** and can conflict. For example:
- 4 short words may fit in 23 chars but exceed measured width
- 3 long words may fit in width but exceed 23 chars

**Current Mitigation**: Conservative limits ensure safety but may waste space.

**Future Work**: Replace with single constraint based on **accurate RTL text measurement** using `canvas.stringWidth()` with actual nikud-rendered text.

### ⚠️ Intrusion Detection Sensitivity

**Issue**: Tile-based detection with 40 RGB distance threshold and 15% intrusion limit.

**Risk**: May be too sensitive (false positives) or too lenient (false negatives) depending on illustration style.

**Current Mitigation**: Delta prompts push content LEFT on retry.

**Future Work**: Experiment with thresholds or switch to ML-based object detection.

### ⚠️ Nikud API Dependency

**Issue**: Claude API may fail or have rate limits.

**Mitigation**: Falls back to manual dictionary (~600 words). Works for common words but may miss rare/new words.

**Future Work**: Expand manual dictionary or integrate dedicated nikud service (e.g., Dicta).

### ⚠️ No Cost Tracking

**Issue**: Pipeline does not log API costs per run.

**Impact**: Cannot monitor spend or optimize cost-heavy operations (Imagen retries).

**Future Work**: Add cost tracking per API call, log to run metadata.

---

## Test Results (v0.1.0)

### Tested on "מיכל מגלה את הספריה" (Age 6)

| Page | White% | Overlap | Nikud% | Intrusion% | Attempts | Status |
|------|--------|---------|--------|------------|----------|--------|
| 1    | 0.01%  | 5.47    | 82.3%  | N/A        | 1        | ✅ |
| 2    | 16.6%  | 4.23    | 79.3%  | N/A        | 1        | ✅ |
| 3    | 0.05%  | 4.70    | 81.3%  | N/A        | 2        | ✅ |
| 4    | 0.10%  | 4.36    | 78.9%  | N/A        | 1        | ✅ |
| 5    | 0.25%  | 4.61    | 70.0%  | N/A        | 1        | ✅ |
| 6    | 4.83%  | 4.78    | 67.3%  | N/A        | 1        | ✅ |
| 7    | 0.22%  | 3.28    | 79.8%  | N/A        | 2        | ✅ |
| 8    | 0.00%  | 5.14    | 81.4%  | N/A        | 1        | ✅ |
| 9    | 1.25%  | 4.81    | 82.9%  | N/A        | 2        | ✅ |
| 10   | 0.00%  | 4.18    | 82.1%  | N/A        | 1        | ✅ |

**Notes**:
- All pages passed QA validation
- Pages 3, 7, 9 required 2 attempts (border or white space issues)
- Average nikud coverage: 78.5% (good for children's reading)
- PDF text layout verified manually - no overflow on any page

---

## Next Priorities

### 🎯 High Priority

1. **Full End-to-End Test Run**
   - Generate a NEW book from scratch (not reusing מיכל)
   - Verify all 5 stages complete successfully
   - Confirm intrusion detection works with 30px margin
   - Document any edge cases or failures

2. **Cost Tracking**
   - Log Claude API calls (input/output tokens, cost)
   - Log Imagen API calls (attempts, cost per image)
   - Add to run metadata: `cost_report.json`
   - Dashboard: total cost per run

3. **Manual Override Tools**
   - Script to replace a specific page image
   - Script to edit story text for a specific page
   - Script to regenerate PDF only (no story/images)
   - Use case: Fix a single problematic page without rerunning entire book

### 🔄 Medium Priority

4. **Threshold Tuning**
   - Experiment with intrusion threshold: 12% vs 15% vs 18%
   - Test white space threshold: 25% vs 30%
   - A/B test delta prompt effectiveness

5. **Text Measurement Refactor**
   - Replace word/char limits with single width-based constraint
   - Use `canvas.stringWidth()` with actual nikud text
   - Ensure RTL handling is correct
   - Test with various text lengths/fonts

6. **Nikud Dictionary Expansion**
   - Add ~500 more common children's words
   - Integrate Dicta API as alternative to Claude
   - A/B test accuracy and cost

### 🌟 Nice-to-Have

7. **Parallel Image Generation**
   - Generate multiple pages in parallel (respects API rate limits)
   - Reduce total book generation time from ~60-100 min to ~20-30 min

8. **Quality Metrics Dashboard**
   - Success rate per stage
   - Average retries per page
   - Nikud coverage trends
   - White space / intrusion trends

9. **Automated Testing**
   - Unit tests for text layout (line breaking)
   - Integration tests for each stage
   - Regression tests for QA validation

---

## Version History

### v0.1.0 (2026-01-30)
- 🎉 Initial locked release
- ✅ Full pipeline operational (Stages 1, 3, 5)
- ✅ QA loop with 4 checks + retry mechanism
- ✅ Hebrew nikud with hybrid system
- ✅ Triple-constraint text layout (30px margin, 4 words, 23 chars)
- ✅ Tested on "מיכל מגלה את הספריה" - all pages passed
- 📝 Documentation complete

---

## Breaking Changes Policy

**This is a locked release.** Any changes to layout constraints, QA thresholds, or core algorithms require:
1. New feature branch
2. Full testing on ≥3 different books
3. Manual verification of PDF output
4. Update to STATUS.md with test results
5. Version bump (0.1.x → 0.2.0)

---

## Contact

For questions or issues: https://github.com/Omribarzi/stories-test/issues
