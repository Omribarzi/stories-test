#!/usr/bin/env python3
"""
Topic Classification & Contextual Adult Role Policy
מנגנון classification של נושאים + העדפות adult role לפי הקשר
"""
from typing import Dict, List, Optional


# ========================================
# Topic Categories & Adult Role Preferences
# ========================================

TOPIC_CATEGORIES = {
    "sleep_regulation": {
        "keywords": ["שינה", "לישון", "עייף", "ישן", "מיטה", "לילה", "חושך", "הרדמה", "להירדם"],
        "description": "Sleep, fatigue, bedtime, calming down",
        "adult_role_preferences": {
            "preferred": ["observes_silently", "regulated_presence"],
            "discouraged": ["participates_actively", "gives_direct_instruction"],
            "rationale": "Quiet presence provides regulation; active involvement can be intrusive"
        }
    },

    "emotional_conflict": {
        "keywords": ["כעס", "כועס", "תסכול", "מתוסכל", "עצבני", "צועק", "זועף", "רוגז"],
        "description": "Anger, frustration, emotional dysregulation",
        "adult_role_preferences": {
            "preferred": ["provides_gentle_support", "models_behavior"],
            "discouraged": ["observes_silently", "validates_explicitly"],
            "rationale": "Active guidance needed; silent observation insufficient"
        }
    },

    "fear_anxiety": {
        "keywords": ["פחד", "מפחד", "חושש", "דאגה", "מודאג", "חרדה", "מפחיד", "נבהל"],
        "description": "Fear, worry, anxiety",
        "adult_role_preferences": {
            "preferred": ["provides_gentle_support", "observes_silently"],
            "discouraged": ["gives_direct_instruction", "validates_explicitly"],
            "rationale": "Calm presence or gentle support; avoid over-explanation"
        }
    },

    "skill_acquisition": {
        "keywords": ["בונה", "מנסה", "לומד", "מצייר", "יוצר", "עושה", "מתאמן", "מתאמץ"],
        "description": "Learning, building, trying, creating",
        "adult_role_preferences": {
            "preferred": ["participates_actively", "models_behavior"],
            "discouraged": ["observes_silently"],
            "rationale": "Active participation or demonstration enhances learning"
        }
    },

    "social_repair": {
        "keywords": ["חבר", "חברות", "ריב", "מריבה", "פיוס", "מתנצל", "סליחה", "התנצלות"],
        "description": "Friendship, conflict resolution, apology",
        "adult_role_preferences": {
            "preferred": ["provides_gentle_support", "models_behavior"],
            "discouraged": ["gives_direct_instruction", "observes_silently"],
            "rationale": "Guidance needed, but not directive; modeling works well"
        }
    },

    "loss_grief": {
        "keywords": ["אובדן", "פרידה", "נפרד", "עזב", "הלך", "מת", "נעלם", "חסר", "געגוע"],
        "description": "Loss, separation, grief, missing",
        "adult_role_preferences": {
            "preferred": ["observes_silently", "provides_gentle_support"],
            "discouraged": ["participates_actively", "validates_explicitly"],
            "rationale": "Space for processing; gentle presence preferred over active involvement"
        }
    },

    "sibling_jealousy": {
        "keywords": ["אח", "אחות", "תינוק", "קנאה", "מקנא", "רואה אותי", "שוכח אותי"],
        "description": "Sibling rivalry, jealousy, feeling unseen",
        "adult_role_preferences": {
            "preferred": ["participates_actively", "provides_gentle_support"],
            "discouraged": ["observes_silently", "validates_explicitly"],
            "rationale": "Active engagement helps child feel seen; validation labels to avoid"
        }
    },

    "autonomy_independence": {
        "keywords": ["לבד", "בעצמי", "אני יכול", "בלי עזרה", "לא צריך", "גדול"],
        "description": "Autonomy, independence, doing alone",
        "adult_role_preferences": {
            "preferred": ["observes_silently", "provides_gentle_support"],
            "discouraged": ["participates_actively", "gives_direct_instruction"],
            "rationale": "Space to try alone; intervention can undermine autonomy"
        }
    }
}


def classify_topic(topic: str) -> Optional[str]:
    """
    מסווג נושא לפי מילות מפתח

    Args:
        topic: תיאור הנושא של הסיפור

    Returns:
        שם הקטגוריה או None
    """
    topic_lower = topic.lower()

    # ספור matches לכל קטגוריה
    matches = {}
    for category, info in TOPIC_CATEGORIES.items():
        count = sum(1 for keyword in info["keywords"] if keyword in topic_lower)
        if count > 0:
            matches[category] = count

    # החזר את הקטגוריה עם הכי הרבה matches
    if matches:
        return max(matches, key=matches.get)

    return None


def get_adult_role_preferences(topic: str) -> Optional[Dict]:
    """
    מחזיר את העדפות adult role לפי הנושא

    Args:
        topic: תיאור הנושא

    Returns:
        דיקט עם preferred, discouraged, rationale או None
    """
    category = classify_topic(topic)
    if category and category in TOPIC_CATEGORIES:
        return TOPIC_CATEGORIES[category]["adult_role_preferences"]
    return None


def should_force_adult_role_variation(topic: str, current_role: str, recent_roles: Dict) -> bool:
    """
    מחליט האם לכפות variation ב-adult role

    Args:
        topic: נושא הסיפור
        current_role: התפקיד שזוהה בסיפור
        recent_roles: התפלגות תפקידים ב-N סיפורים אחרונים

    Returns:
        True אם צריך לכפות variation
    """
    # בדוק אם יש contextual preferences
    prefs = get_adult_role_preferences(topic)

    if prefs:
        # אם התפקיד הנוכחי הוא preferred - אל תכפה שינוי
        if current_role in prefs["preferred"]:
            return False

        # אם התפקיד discouraged - כפה שינוי רק אם הוא גם overused
        if current_role in prefs["discouraged"]:
            total = sum(recent_roles.values())
            count = recent_roles.get(current_role, 0)
            return total > 0 and count / total > 0.5

    # fallback: כפה variation אם > 50% overused
    total = sum(recent_roles.values())
    if total > 0:
        for role, count in recent_roles.items():
            if count / total > 0.5 and role == current_role:
                return True

    return False


def get_contextual_message(topic: str, violated_role: str) -> str:
    """
    מייצר הודעה contextual למצב שבו התפקיד לא מתאים לנושא

    Args:
        topic: נושא הסיפור
        violated_role: התפקיד שזוהה (ולא מתאים)

    Returns:
        הודעה מותאמת
    """
    category = classify_topic(topic)

    if category and category in TOPIC_CATEGORIES:
        prefs = TOPIC_CATEGORIES[category]["adult_role_preferences"]
        preferred = ", ".join(prefs["preferred"])
        rationale = prefs["rationale"]

        return f"""
🎯 CONTEXTUAL GUIDANCE for topic category '{category}':

PREFERRED adult roles for this topic: {preferred}
REASON: {rationale}

Your story used '{violated_role}' which may not fit this emotional context.
Consider using one of the preferred roles instead.
"""

    return ""


def explain_fallback(topic: str, final_role: str, attempts: int) -> Dict:
    """
    מסביר למה fallback התקבל (semantic win, not failure)

    Args:
        topic: נושא הסיפור
        final_role: התפקיד שנבחר בסוף
        attempts: מספר ניסיונות

    Returns:
        דיקט עם הסבר ו-status
    """
    prefs = get_adult_role_preferences(topic)

    if prefs and final_role in prefs["preferred"]:
        return {
            "status": "contextual_win",
            "message": f"Model insisted on '{final_role}' which is contextually appropriate for this topic",
            "confidence": "high",
            "rationale": prefs["rationale"]
        }
    elif prefs and final_role in prefs["discouraged"]:
        return {
            "status": "contextual_mismatch",
            "message": f"Model chose '{final_role}' despite it being discouraged for this topic",
            "confidence": "low",
            "rationale": f"Preferred: {', '.join(prefs['preferred'])}"
        }
    else:
        return {
            "status": "neutral_fallback",
            "message": f"Model chose '{final_role}' after {attempts} attempts",
            "confidence": "medium",
            "rationale": "No strong contextual preference for this topic"
        }


if __name__ == "__main__":
    # בדיקות
    test_topics = [
        "ילד בן 4 שמתקשה להירדם בלילה",
        "ילדה בת 5 שמרגישה כעס כשדברים לא הולכים כמו שהיא רוצה",
        "ילד בן 3 שמפחד מהחושך",
        "ילדה בת 6 שלומדת לבנות מגדל גבוה",
    ]

    for topic in test_topics:
        print(f"\nTopic: {topic}")
        category = classify_topic(topic)
        print(f"Category: {category}")

        if category:
            prefs = get_adult_role_preferences(topic)
            print(f"Preferred: {prefs['preferred']}")
            print(f"Discouraged: {prefs['discouraged']}")
            print(f"Rationale: {prefs['rationale']}")
