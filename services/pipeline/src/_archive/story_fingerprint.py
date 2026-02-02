#!/usr/bin/env python3
"""
Story Fingerprint Extractor
מחלץ "טביעת אצבע" של סיפור לזיהוי דפוסים חוזרים
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def extract_conflict_type(story: Dict) -> str:
    """מזהה את סוג הקונפליקט המרכזי"""
    pages_text = " ".join([p["text"] for p in story["pages"]]).lower()

    # מילות מפתח לזיהוי קונפליקטים
    conflict_patterns = {
        "fear_of_new": ["חדש", "מפחד", "לא מכיר", "ראשון"],
        "loss_grief": ["מת", "נעלם", "אבד", "נפרד", "לא יתעורר"],
        "social_isolation": ["לבד", "אף אחד", "בודד", "לא משחק"],
        "anger_frustration": ["כועס", "לא רוצה", "מכה", "זורק"],
        "change_transition": ["עובר", "משתנה", "עוזב", "מתחיל"],
        "self_regulation": ["חיתול", "שינה", "אוכל", "לא מצליח"]
    }

    for conflict_type, keywords in conflict_patterns.items():
        if any(kw in pages_text for kw in keywords):
            return conflict_type

    return "general_emotional"


def extract_truth_moment_type(story: Dict) -> str:
    """מזהה את סוג רגע האמת (truth moment)"""
    pages = story["pages"]
    mid_section = pages[len(pages)//2:]  # חצי שני של הסיפור

    truth_patterns = {
        "creates_physical_solution": ["בונה", "עושה", "שם", "מניח", "ממלא"],
        "makes_internal_decision": ["מחליט", "בוחר", "חושב", "מרגיש"],
        "takes_action_alone": ["הולך", "ניגש", "קם", "עושה בעצמו"],
        "connects_with_other": ["מתיישב", "מתקרב", "נותן", "משתף"],
        "accepts_situation": ["נשאר", "מסתכל", "שותק", "מקבל"]
    }

    for page in mid_section:
        text = page["text"].lower()
        for truth_type, keywords in truth_patterns.items():
            if any(kw in text for kw in keywords):
                return truth_type

    return "observes_and_processes"


def extract_solution_mechanism(story: Dict) -> str:
    """מזהה את מנגנון הפתרון"""
    pages_text = " ".join([p["text"] for p in story["pages"]]).lower()

    solution_patterns = {
        "physical_object_comfort": ["כוס", "כרית", "שמיכה", "חפץ", "אבן", "משהו"],
        "parallel_activity": ["ליד", "יחד", "גם", "בונה", "עושה"],
        "adult_presence": ["אמא", "אבא", "מורה", "עומד", "מסתכל"],
        "self_initiated_action": ["בעצמו", "לבד", "קם", "הולך"],
        "time_and_repetition": ["שוב", "עוד", "כל יום", "ממשיך"]
    }

    for mechanism, keywords in solution_patterns.items():
        if any(kw in pages_text for kw in keywords):
            return mechanism

    return "internal_processing"


def extract_adult_role(story: Dict) -> str:
    """מזהה את תפקיד המבוגר - בוחר בדפוס הדומיננטי"""
    pages_text = " ".join([p["text"] for p in story["pages"]]).lower()

    if "אמא" not in pages_text and "אבא" not in pages_text and "מורה" not in pages_text:
        return "no_adult_present"

    # ספור מילות מפתח לכל תפקיד (חיפוש מדויק יותר)
    adult_patterns = {
        "validates_explicitly": ["כל הכבוד", "יפה מאוד", "מצוין", "ילד גדול", "ילדה גדולה", "אח גדול טוב", "אחות גדולה טובה", "נהדר", "גאה בך"],
        "gives_direct_instruction": ["אומר ל", "מסביר", "מראה ל", "מלמד"],
        "participates_actively": ["משחק", "בונה", "מוציא", "נותן", "עושה יחד"],
        "provides_gentle_support": ["שואל", "מתקרב", "יושב ל", "מחייך", "מנהנ"],
        "observes_silently": ["רואה", "מסתכל", "עומד ו", "לא אומר"]
    }

    # ספור matches לכל קטגוריה
    role_scores = {}
    for role, keywords in adult_patterns.items():
        count = sum(1 for kw in keywords if kw in pages_text)
        if count > 0:
            role_scores[role] = count

    # אם יש validation מפורש - זה תמיד הכי בעייתי
    if "validates_explicitly" in role_scores:
        return "validates_explicitly"

    # אחרת, החזר את הדומיננטי
    if role_scores:
        return max(role_scores, key=role_scores.get)

    return "background_presence"


def extract_pacing_profile(story: Dict) -> str:
    """מזהה את פרופיל הקצב"""
    pages = story["pages"]

    # ספירת משפטים בכל עמוד
    sentence_counts = []
    for page in pages:
        text = page["text"]
        sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
        sentence_counts.append(len(sentences))

    # ניתוח דפוסי תנועה
    movement_words = ["רץ", "הולך", "קופץ", "נע", "עובר"]
    stillness_words = ["יושב", "עומד", "שוכב", "מסתכל", "שותק"]

    movement_count = sum(1 for p in pages if any(w in p["text"].lower() for w in movement_words))
    stillness_count = sum(1 for p in pages if any(w in p["text"].lower() for w in stillness_words))

    if stillness_count > movement_count * 2:
        return "slow_contemplative"
    elif movement_count > stillness_count * 2:
        return "active_energetic"
    else:
        return "balanced_mixed"


def extract_ending_tone(story: Dict) -> str:
    """מזהה את טון הסיום"""
    last_pages = story["pages"][-3:]  # 3 עמודים אחרונים
    text = " ".join([p["text"] for p in last_pages]).lower()

    ending_patterns = {
        "open_continuation": ["מחר", "עוד", "עד", "ממשיך"],
        "quiet_closure": ["שקט", "נרדם", "שוכב", "סוגר עיניים"],
        "gentle_resolution": ["בסדר", "טוב", "יפה", "נרגע"],
        "energetic_celebration": ["יש", "הצלחתי", "כל הכבוד"]
    }

    for tone, keywords in ending_patterns.items():
        if any(kw in text for kw in keywords):
            return tone

    return "neutral_ending"


def extract_symbolic_object(story: Dict) -> Optional[str]:
    """מזהה חפץ סמלי מרכזי (אם יש)"""
    pages_text = " ".join([p["text"] for p in story["pages"]]).lower()

    # חפשים שמופיעים מספר פעמים
    objects = ["כוס", "כרית", "שמיכה", "אבן", "עץ", "פינה", "חדר", "מיטה"]

    for obj in objects:
        if pages_text.count(obj) >= 3:  # מופיע לפחות 3 פעמים
            return obj

    return None


def extract_fingerprint(story_data: Dict,
                       story_id: str,
                       series: Optional[str] = None,
                       series_angle: Optional[str] = None) -> Dict:
    """
    מחלץ fingerprint מלא של סיפור

    Args:
        story_data: הסיפור המלא (מבנה JSON)
        story_id: מזהה ייחודי
        series: שם הסדרה (אם חלק מסדרה)
        series_angle: הזווית הספציפית בסדרה

    Returns:
        Fingerprint מלא
    """
    story = story_data["story"]

    fingerprint = {
        "story_id": story_id,
        "title": story["title"],
        "target_age": story["target_age"],
        "created_at": datetime.now().isoformat(),

        # Series support (optional)
        "series": series,
        "series_angle": series_angle,

        # Pattern fingerprints
        "patterns": {
            "conflict_type": extract_conflict_type(story),
            "truth_moment_type": extract_truth_moment_type(story),
            "solution_mechanism": extract_solution_mechanism(story),
            "adult_role": extract_adult_role(story),
            "pacing_profile": extract_pacing_profile(story),
            "ending_tone": extract_ending_tone(story),
            "symbolic_object": extract_symbolic_object(story)
        }
    }

    return fingerprint


def save_fingerprint(fingerprint: Dict, history_file: Path = None):
    """שומר fingerprint להיסטוריה"""
    if history_file is None:
        history_file = Path(__file__).parent.parent / "data" / "fingerprints" / "fingerprints_history.json"

    # צור תיקייה אם לא קיימת
    history_file.parent.mkdir(parents=True, exist_ok=True)

    # טען היסטוריה קיימת
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {"stories": []}

    # הוסף fingerprint חדש
    history["stories"].append(fingerprint)

    # שמור
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return history_file


def load_fingerprints(n: int = None,
                     series: str = None,
                     history_file: Path = None) -> List[Dict]:
    """
    טוען fingerprints מההיסטוריה

    Args:
        n: מספר אחרונים (None = הכל)
        series: סדרה ספציפית (None = הכל)
        history_file: נתיב לקובץ היסטוריה

    Returns:
        רשימת fingerprints
    """
    if history_file is None:
        history_file = Path(__file__).parent.parent / "data" / "fingerprints" / "fingerprints_history.json"

    if not history_file.exists():
        return []

    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)

    stories = history["stories"]

    # סנן לפי סדרה אם צריך
    if series:
        stories = [s for s in stories if s.get("series") == series]

    # קח N אחרונים אם צריך
    if n:
        stories = stories[-n:]

    return stories


if __name__ == "__main__":
    # בדיקה: חלץ fingerprint מסיפור קיים
    story_file = Path("data/stories/יואב_age5/story_generic_20260129_133216.json")

    if story_file.exists():
        with open(story_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        fingerprint = extract_fingerprint(
            story_data,
            story_id="yoav_age5_20260129_133216",
            series=None,
            series_angle=None
        )

        print("📌 Fingerprint extracted:")
        print(json.dumps(fingerprint, ensure_ascii=False, indent=2))

        # שמור
        saved_path = save_fingerprint(fingerprint)
        print(f"\n✅ Fingerprint saved to: {saved_path}")
    else:
        print(f"❌ Story file not found: {story_file}")
