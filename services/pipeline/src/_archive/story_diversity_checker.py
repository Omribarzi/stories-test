#!/usr/bin/env python3
"""
Story Diversity Checker
בודק חזרתיות בדפוסים של סיפורים
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter
from story_fingerprint import load_fingerprints


def check_solution_repetition(new_patterns: Dict, last_n: List[Dict], threshold: int = 3) -> Optional[str]:
    """
    בודק חזרה של אותו מנגנון פתרון

    Args:
        new_patterns: הדפוסים של הסיפור החדש
        last_n: N סיפורים אחרונים
        threshold: מספר מקסימלי של חזרות מותרות

    Returns:
        אזהרה או None
    """
    new_mechanism = new_patterns["solution_mechanism"]

    # ספור כמה פעמים המנגנון הזה מופיע ב-N אחרונים
    mechanisms = [s["patterns"]["solution_mechanism"] for s in last_n]
    count = mechanisms.count(new_mechanism)

    if count >= threshold:
        return f"⚠️  Solution mechanism '{new_mechanism}' appears in {count}/{len(last_n)} recent stories"

    return None


def check_structure_repetition(new_patterns: Dict, last_n: List[Dict], threshold: int = 2) -> Optional[str]:
    """בודק חזרה של אותו מבנה רגשי (combo של conflict + truth_moment + ending)"""

    new_structure = f"{new_patterns['conflict_type']}→{new_patterns['truth_moment_type']}→{new_patterns['ending_tone']}"

    structures = []
    for s in last_n:
        p = s["patterns"]
        structures.append(f"{p['conflict_type']}→{p['truth_moment_type']}→{p['ending_tone']}")

    count = structures.count(new_structure)

    if count >= threshold:
        return f"🔴 CRITICAL: Identical emotional structure in {count}/{len(last_n)} recent stories"

    return None


def check_adult_role_repetition(new_patterns: Dict, last_n: List[Dict]) -> Optional[str]:
    """בודק אם תפקיד המבוגר זהה בכל הסיפורים"""

    new_role = new_patterns["adult_role"]

    roles = [s["patterns"]["adult_role"] for s in last_n]

    # אם כל N סיפורים אחרונים עם אותו תפקיד מבוגר
    if len(set(roles)) == 1 and roles[0] == new_role:
        return f"⚠️  Adult role '{new_role}' is identical in ALL {len(last_n)} recent stories"

    return None


def check_pacing_repetition(new_patterns: Dict, last_n: List[Dict], threshold: int = 4) -> Optional[str]:
    """בודק חזרה של אותו קצב"""

    new_pacing = new_patterns["pacing_profile"]

    pacings = [s["patterns"]["pacing_profile"] for s in last_n]
    count = pacings.count(new_pacing)

    if count >= threshold:
        return f"⚠️  Pacing '{new_pacing}' appears in {count}/{len(last_n)} recent stories"

    return None


def check_ending_repetition(new_patterns: Dict, last_n: List[Dict]) -> Optional[str]:
    """בודק אם כל הסיפורים מסתיימים באותו טון"""

    new_ending = new_patterns["ending_tone"]

    endings = [s["patterns"]["ending_tone"] for s in last_n]

    if len(set(endings)) == 1 and endings[0] == new_ending:
        return f"🔴 CRITICAL: All {len(last_n)} recent stories end with '{new_ending}'"

    return None


def check_symbolic_object_repetition(new_patterns: Dict, last_n: List[Dict], threshold: int = 2) -> Optional[str]:
    """בודק חזרה של אותו חפץ סמלי"""

    new_object = new_patterns.get("symbolic_object")

    if not new_object:
        return None  # אין חפץ סמלי בסיפור החדש

    objects = [s["patterns"].get("symbolic_object") for s in last_n if s["patterns"].get("symbolic_object")]
    count = objects.count(new_object)

    if count >= threshold:
        return f"⚠️  Symbolic object '{new_object}' appears in {count}/{len(last_n)} recent stories"

    return None


def check_external_cliches(story_text: str) -> List[str]:
    """
    בודק קלישאות מהספרות החיצונית

    Args:
        story_text: כל הטקסט של הסיפור

    Returns:
        רשימת קלישאות שנמצאו
    """
    # Blacklist - רק דוגמאות ברורות, לא רשימה ממצה
    # המטרה: לתפוס את הדוגמאות הגרועות ביותר, לא לכסות הכל
    blacklist = [
        "כולם יכולים להיות חברים",
        "גם לי היה קשה כשהייתי",
        "הוא למד ש",
        "עכשיו היא יודעת ש",
        "עכשיו הוא יודע ש",
        "בסוף הכול הסתדר",
        "הגוף שלך חכם"
    ]

    found_cliches = []
    text_lower = story_text.lower()

    for cliche in blacklist:
        if cliche.lower() in text_lower:
            found_cliches.append(cliche)

    return found_cliches


def generate_diversity_note(warnings: List[str]) -> str:
    """
    מייצר הערת diversity לפרומפט

    Args:
        warnings: רשימת אזהרות

    Returns:
        טקסט להוסיף לפרומפט
    """
    if not warnings:
        return ""

    note = "\n\n🚨 DIVERSITY REQUIREMENT - CRITICAL:\n\n"

    for warning in warnings:
        note += f"  • {warning}\n"

    note += "\n⚡ YOU MUST explore a different approach for THIS story.\n"
    note += "These patterns are OVERUSED. Try: different solution mechanism, different adult role, different ending tone.\n"
    note += "This is NOT optional - you should vary UNLESS this specific topic absolutely requires this exact pattern.\n"
    note += "Quality is still priority #1, but within quality standards - VARY the approach.\n"

    return note


def check_internal_diversity(new_fingerprint: Dict,
                             n: int = 5,
                             series: str = None) -> Dict:
    """
    בדיקת חזרתיות פנימית (מול הסיפורים שלך)

    Args:
        new_fingerprint: טביעת אצבע של הסיפור החדש
        n: מספר סיפורים אחרונים לבדוק
        series: סדרה ספציפית (אם רלוונטי)

    Returns:
        דיקט עם warnings ו-diversity note
    """
    # טען N אחרונים
    last_n = load_fingerprints(n=n, series=series)

    if len(last_n) < 3:
        # אין מספיק היסטוריה
        return {
            "warnings": [],
            "diversity_note": "",
            "status": "insufficient_history"
        }

    new_patterns = new_fingerprint["patterns"]
    warnings = []

    # בדיקה 1: פתרון סמלי
    w = check_solution_repetition(new_patterns, last_n, threshold=3)
    if w:
        warnings.append(w)

    # בדיקה 2: מבנה רגשי
    w = check_structure_repetition(new_patterns, last_n, threshold=2)
    if w:
        warnings.append(w)

    # בדיקה 3: תפקיד מבוגר
    w = check_adult_role_repetition(new_patterns, last_n)
    if w:
        warnings.append(w)

    # בדיקה 4: קצב
    w = check_pacing_repetition(new_patterns, last_n, threshold=4)
    if w:
        warnings.append(w)

    # בדיקה 5: סיום
    w = check_ending_repetition(new_patterns, last_n)
    if w:
        warnings.append(w)

    # בדיקה 6: חפץ סמלי
    w = check_symbolic_object_repetition(new_patterns, last_n, threshold=2)
    if w:
        warnings.append(w)

    # צור diversity note
    diversity_note = generate_diversity_note(warnings)

    status = "critical" if any("CRITICAL" in w for w in warnings) else \
             "warning" if warnings else \
             "ok"

    return {
        "warnings": warnings,
        "diversity_note": diversity_note,
        "status": status,
        "last_n_analyzed": len(last_n)
    }


def check_external_cliches_full(story_data: Dict) -> Dict:
    """
    בדיקת קלישאות חיצוניות

    Args:
        story_data: הסיפור המלא

    Returns:
        דיקט עם קלישאות שנמצאו
    """
    # חבר את כל הטקסט
    pages = story_data["story"]["pages"]
    full_text = " ".join([p["text"] for p in pages])

    cliches = check_external_cliches(full_text)

    if cliches:
        return {
            "found_cliches": cliches,
            "status": "fail",
            "message": f"Found {len(cliches)} external cliches"
        }
    else:
        return {
            "found_cliches": [],
            "status": "pass",
            "message": "No external cliches found"
        }


def analyze_recent_patterns(n: int = 5, series: str = None) -> Dict:
    """
    מנתח דפוסים אחרונים (לשימוש אנליטי)

    Returns:
        סיכום של הדפוסים האחרונים
    """
    last_n = load_fingerprints(n=n, series=series)

    if len(last_n) < 3:
        return {"status": "insufficient_history"}

    # אסוף סטטיסטיקות
    conflicts = [s["patterns"]["conflict_type"] for s in last_n]
    truth_moments = [s["patterns"]["truth_moment_type"] for s in last_n]
    solutions = [s["patterns"]["solution_mechanism"] for s in last_n]
    adult_roles = [s["patterns"]["adult_role"] for s in last_n]
    endings = [s["patterns"]["ending_tone"] for s in last_n]

    return {
        "analyzed": len(last_n),
        "conflicts": dict(Counter(conflicts)),
        "truth_moments": dict(Counter(truth_moments)),
        "solutions": dict(Counter(solutions)),
        "adult_roles": dict(Counter(adult_roles)),
        "endings": dict(Counter(endings))
    }


if __name__ == "__main__":
    # בדיקה: נתח דפוסים אחרונים
    print("📊 Analyzing recent patterns...")
    analysis = analyze_recent_patterns(n=10)

    if analysis.get("status") == "insufficient_history":
        print("⚠️  Not enough history to analyze")
    else:
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
