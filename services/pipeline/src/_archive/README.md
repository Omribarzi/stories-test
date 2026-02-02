# Archive - קבצים שלא בשימוש פעיל

הועברו לכאן ב-2026-02-01. אף אחד מהקבצים האלה לא מיובא ע"י הפייפליין הפעיל
(`run_full_book_10pages.py` / `test_story_quality.py`).

## הוחלפו בגרסאות חדשות

| קובץ ישן | הוחלף ע"י |
|---|---|
| `orchestrator.py` | `run_full_book_10pages.py` |
| `orchestrator_optimized.py` | `run_full_book_10pages.py` |
| `run_manager.py` | `RunManager` class ב-`run_full_book_10pages.py` |
| `production_pdf_generator.py` | `production_pdf_with_nikud.py` |
| `production_image_generator.py` | `image_generator.py` |
| `gemini_agent.py` | `image_generator.py` |

## כלי עזר שלא שולבו (אפשר לשחזר בעתיד)

| קובץ | תיאור | שווה לחזור? |
|---|---|---|
| `story_diversity_checker.py` | בדיקת גיוון בין סיפורים | כן - כשנייצר בכמויות |
| `story_fingerprint.py` | fingerprint לזיהוי סיפורים דומים | כן - תלות של diversity_checker |
| `cost_optimizer.py` | אופטימיזציית עלויות API | אולי - לוגיקה בסיסית כבר ב-COST_MODE_PRESETS |
| `story_arc_analyzer.py` | ניתוח מבנה עלילה והנחיות ויזואליות | אולי - לשלב image generation |
| `advanced_prompt_enhancer.py` | שיפור פרומפטים אוטומטי | לא סביר |
| `story_personalizer.py` | התאמה אישית לילד (החלפת שם) | לא - הפייפליין מייצר מותאם מההתחלה |
| `story_personalizer_smart.py` | התאמה אישית עם Claude per-page | לא - יקר ומיותר |
| `character_analyzer.py` | ניתוח דמויות | לא סביר |
| `topic_classification.py` | סיווג נושאים | לא סביר |
| `improved_composition_prompts.py` | פרומפטים לקומפוזיציית תמונה | אולי |
| `nikud_dictionary.py` | מילון ניקוד | לא - הוחלף ב-hebrew_nikud_renderer |
| `text_on_image_renderer.py` | רנדור טקסט על תמונה | לא - הוחלף ב-production_pdf_with_nikud |
