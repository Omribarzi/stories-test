#!/usr/bin/env python3
"""
מנהל ריצות - Run Manager
מטפל ב-run_id, תיקיות, schema, ולוגים
"""
from pathlib import Path
from datetime import datetime
import json
import hashlib
from typing import Dict, Optional


class InputContractError(RuntimeError):
    """חריגה לכשלי contract בין CLI לבין story input"""
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


class RunManager:
    """
    מנהל ריצה אחת של ייצור ספר
    """

    STORY_SCHEMA_VERSION = "1.0"

    @staticmethod
    def validate_input_contract(
        story_data: dict,
        expected_age: int,
        expected_name: str | None = None,
        expected_pages: int | None = None
    ):
        """
        בדיקה קשיחה: story מתאים ל-CLI input

        Args:
            story_data: נתוני הסיפור
            expected_age: גיל יעד מה-CLI
            expected_name: שם הדמות מה-CLI (אופציונלי)
            expected_pages: מספר עמודים צפוי (אופציונלי)

        Raises:
            InputContractError: אם יש אי-התאמה
        """
        if "story" not in story_data:
            raise InputContractError("INPUT_SCHEMA_INVALID", "Missing 'story' root key")

        story = story_data["story"]

        # בדיקת target_age חובה
        if "target_age" not in story:
            raise InputContractError("INPUT_SCHEMA_INVALID", "Missing story.target_age")

        actual_age = story["target_age"]
        if actual_age != expected_age:
            raise InputContractError(
                "INPUT_MISMATCH_AGE",
                f"Story age={actual_age}, CLI age={expected_age}"
            )

        # בדיקת pages חובה
        pages = story.get("pages")
        if not isinstance(pages, list) or len(pages) == 0:
            raise InputContractError("INPUT_SCHEMA_INVALID", "story.pages missing or empty")

        # בדיקת מספר עמודים אם צוין
        if expected_pages is not None and len(pages) != expected_pages:
            raise InputContractError(
                "INPUT_MISMATCH_PAGES",
                f"Story pages={len(pages)}, expected={expected_pages}"
            )

        # בדיקת שם דמות אם צוין
        if expected_name:
            full_text = "\n".join(p.get("text", "") for p in pages)
            name_count = full_text.count(expected_name)
            if name_count == 0:
                raise InputContractError(
                    "INPUT_MISMATCH_NAME",
                    f"Expected name '{expected_name}' not found in story text"
                )

    def __init__(self, topic: str, age: int, name: str, base_dir: Path = None):
        """
        יוצר run_id ומבנה תיקיות

        Args:
            topic: נושא הספר
            age: גיל יעד
            name: שם הדמות
            base_dir: תיקייה בסיס (ברירת מחדל: data/runs)
        """
        # יצירת run_id: YYYYMMDD_HHMMSS_<hash>
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_hash = hashlib.md5(topic.encode()).hexdigest()[:6]
        self.run_id = f"{timestamp}_{topic_hash}"

        # book_slug: מזהה נקי
        clean_name = name.replace(" ", "_")
        clean_topic = topic.replace(" ", "_")[:20]
        self.book_slug = f"{clean_name}_age{age}_{clean_topic}"

        # מבנה תיקיות
        if base_dir is None:
            base_dir = Path("data/runs")

        self.base_dir = base_dir / self.book_slug / self.run_id
        self.story_dir = self.base_dir / "story"
        self.images_dir = self.base_dir / "images"
        self.pdf_dir = self.base_dir / "pdf"
        self.qa_dir = self.base_dir / "qa"
        self.logs_dir = self.base_dir / "logs"

        # יצירת תיקיות
        for dir_path in [self.story_dir, self.images_dir, self.pdf_dir,
                         self.qa_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # מטא-דאטה
        self.metadata = {
            "run_id": self.run_id,
            "book_slug": self.book_slug,
            "created_at": datetime.now().isoformat(),
            "topic": topic,
            "age": age,
            "character_name": name,
            "schema_version": self.STORY_SCHEMA_VERSION,
            "status": "RUNNING"
        }

        self._save_metadata()

    def _save_metadata(self):
        """שומר metadata של הריצה"""
        metadata_path = self.base_dir / "run_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def validate_story_schema(self, story_data: dict) -> tuple:
        """
        מוודא שה-story עומד בschema הנדרש

        Returns:
            (is_valid: bool, errors: list)
        """
        errors = []

        # בדיקות חובה
        if 'story' not in story_data:
            errors.append("Missing 'story' key")
            return False, errors

        story = story_data['story']

        # שדות חובה
        required_fields = ['title', 'target_age', 'pages']
        for field in required_fields:
            if field not in story:
                errors.append(f"Missing required field: story.{field}")

        # בדיקת pages
        if 'pages' in story:
            if not isinstance(story['pages'], list):
                errors.append("story.pages must be a list")
            else:
                for i, page in enumerate(story['pages']):
                    if 'page_number' not in page:
                        errors.append(f"Page {i}: missing page_number")
                    if 'text' not in page:
                        errors.append(f"Page {i}: missing text")
                    if 'visual_description' not in page:
                        errors.append(f"Page {i}: missing visual_description")

        # בדיקת rating אם קיים
        if 'rating' in story_data:
            rating = story_data['rating']
            if 'weighted_score' not in rating:
                errors.append("rating.weighted_score missing")

        return len(errors) == 0, errors

    def save_story(self, story_data: dict, version: str = "v1"):
        """
        שומר סיפור אחרי ולידציה

        Args:
            story_data: נתוני הסיפור
            version: גרסה (v1, best, text_checked וכו')
        """
        # וולידציה
        is_valid, errors = self.validate_story_schema(story_data)
        if not is_valid:
            raise ValueError(f"Invalid story schema: {errors}")

        # שמירה
        story_path = self.story_dir / f"story_{version}.json"
        with open(story_path, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)

        return story_path

    def load_story(self, version: str = "best") -> dict:
        """טוען סיפור"""
        story_path = self.story_dir / f"story_{version}.json"
        if not story_path.exists():
            raise FileNotFoundError(f"Story not found: {story_path}")

        with open(story_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def log_step(self, step_name: str, data: dict):
        """
        לוג שלב

        Args:
            step_name: שם השלב (story_generation, text_check, וכו')
            data: נתונים לשמירה
        """
        log_path = self.logs_dir / f"{step_name}_{self.run_id}.json"

        log_entry = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            **data
        }

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)

    def mark_step_complete(self, step_name: str, passed: bool, details: dict = None):
        """
        מסמן שלב כהושלם

        Args:
            step_name: שם השלב
            passed: האם עבר
            details: פרטים נוספים
        """
        if 'steps' not in self.metadata:
            self.metadata['steps'] = {}

        self.metadata['steps'][step_name] = {
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }

        self._save_metadata()

    def mark_failed(self, reason: str):
        """מסמן ריצה כנכשלה"""
        self.metadata['status'] = "FAILED"
        self.metadata['failure_reason'] = reason
        self.metadata['failed_at'] = datetime.now().isoformat()
        self._save_metadata()

    def mark_complete(self):
        """מסמן ריצה כהושלמה בהצלחה"""
        self.metadata['status'] = "COMPLETED"
        self.metadata['completed_at'] = datetime.now().isoformat()
        self._save_metadata()

    def generate_report(self) -> dict:
        """
        יוצר דוח מסכם של הריצה

        Returns:
            dict עם סיכום מלא
        """
        report = {
            "run_id": self.run_id,
            "book_slug": self.book_slug,
            "status": self.metadata.get('status'),
            "created_at": self.metadata.get('created_at'),
            "steps": self.metadata.get('steps', {}),
            "files": {
                "story": [str(p) for p in self.story_dir.glob("*.json")],
                "images": [str(p) for p in self.images_dir.glob("*.png")],
                "pdf": [str(p) for p in self.pdf_dir.glob("*.pdf")],
                "qa": [str(p) for p in self.qa_dir.glob("*.json")]
            },
            "summary": {}
        }

        # ספירת קבצים
        report['summary']['total_images'] = len(report['files']['images'])
        report['summary']['total_pdfs'] = len(report['files']['pdf'])

        # בדיקת הצלחה
        steps = report['steps']
        if steps:
            passed_steps = sum(1 for s in steps.values() if s.get('passed'))
            total_steps = len(steps)
            report['summary']['steps_passed'] = f"{passed_steps}/{total_steps}"

        # שמירת דוח
        report_path = self.qa_dir / "final_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report


# Demo
if __name__ == "__main__":
    # יצירת run
    run = RunManager(
        topic="רועי עובר לעיר אחרת",
        age=7,
        name="רועי"
    )

    print(f"Run ID: {run.run_id}")
    print(f"Book Slug: {run.book_slug}")
    print(f"Base Dir: {run.base_dir}")

    # סימולציה של שלב
    run.mark_step_complete("story_generation", True, {
        "score": 95.5,
        "iterations": 2
    })

    # דוח
    report = run.generate_report()
    print(f"\nReport: {json.dumps(report, indent=2, ensure_ascii=False)}")
