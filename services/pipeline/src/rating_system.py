"""
מערכת דירוג משותפת לשני המודלים
"""
import json
from typing import Dict, List, Tuple
from pathlib import Path


class RatingSystem:
    def __init__(self, criteria_path: str = None):
        if criteria_path is None:
            criteria_path = Path(__file__).parent.parent / "config" / "rating_criteria.json"

        with open(criteria_path, 'r', encoding='utf-8') as f:
            self.criteria = json.load(f)

    def get_rating_prompt(self, rating_type: str) -> str:
        """
        יוצר פרומפט מובנה למתן ציון

        Args:
            rating_type: topic_rating, story_rating, או character_rating
        """
        if rating_type not in self.criteria:
            raise ValueError(f"Unknown rating type: {rating_type}")

        rating_config = self.criteria[rating_type]

        prompt = f"""
{rating_config['description']}

עליך לדרג לפי הקריטריונים הבאים:

"""
        for criterion in rating_config['criteria']:
            prompt += f"""
{criterion['name']} (משקל {criterion['weight']}%):
{criterion['description']}
"""

        prompt += f"""

הוראות דירוג:
1. דרג כל קריטריון בסולם 0-100
2. חשב ציון משוקלל סופי
3. הציון המינימלי לאישור הוא {rating_config['min_score']}

השב בפורמט JSON הבא:
{{
    "scores": {{
        "criterion_name": score,
        ...
    }},
    "weighted_score": final_score,
    "reasoning": "הסבר מפורט לציונים",
    "suggestions": "הצעות לשיפור (אם הציון מתחת ל-{rating_config['min_score']})"
}}
"""
        return prompt

    def calculate_weighted_score(self, scores: Dict[str, float], rating_type: str) -> float:
        """
        מחשב ציון משוקלל
        """
        rating_config = self.criteria[rating_type]
        total_score = 0

        for criterion in rating_config['criteria']:
            criterion_name = criterion['name']
            weight = criterion['weight'] / 100
            score = scores.get(criterion_name, 0)
            total_score += score * weight

        return round(total_score, 2)

    def meets_threshold(self, score: float, rating_type: str) -> bool:
        """
        בודק האם הציון עובר את הסף המינימלי
        """
        min_score = self.criteria[rating_type]['min_score']
        return score >= min_score


# דוגמה לשימוש
if __name__ == "__main__":
    rs = RatingSystem()
    print("=== Topic Rating Prompt ===")
    print(rs.get_rating_prompt("topic_rating"))
    print("\n=== Story Rating Prompt ===")
    print(rs.get_rating_prompt("story_rating"))
