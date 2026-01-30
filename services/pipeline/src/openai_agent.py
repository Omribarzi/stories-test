"""
OpenAI Agent - אחראי על הערכה וביקורת
"""
import os
import json
from openai import OpenAI
from typing import Dict, List
from dotenv import load_dotenv
from rating_system import RatingSystem

load_dotenv()


class OpenAIAgent:
    def __init__(self, model: str = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.rating_system = RatingSystem()

    def rate_topics(self, topics: List[Dict]) -> List[Dict]:
        """
        מעריך רשימת נושאים לפי קריטריוני הדירוג

        Returns:
            רשימת נושאים עם ציונים ומשוב
        """
        rating_prompt = self.rating_system.get_rating_prompt("topic_rating")

        results = []
        for topic in topics:
            system_prompt = """אתה מומחה לחינוך והתפתחות ילדים.
תפקידך להעריך נושאים לספרי ילדים בצורה אובייקטיבית וקפדנית.
היה ביקורתי אך בונה, והצע שיפורים קונקרטיים."""

            user_prompt = f"""העריך את הנושא הבא:

שם: {topic['name']}
תת-נושאים: {', '.join(topic['sub_topics'])}
ערך חינוכי: {topic['educational_value']}
רעיון לעלילה: {topic['story_concept']}

{rating_prompt}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            rating_data = json.loads(response.choices[0].message.content)

            results.append({
                "topic": topic,
                "rating": rating_data,
                "approved": self.rating_system.meets_threshold(
                    rating_data["weighted_score"],
                    "topic_rating"
                )
            })

        return results

    def rate_story(self, story: Dict, topic: Dict) -> Dict:
        """
        מעריך סיפור מלא
        """
        rating_prompt = self.rating_system.get_rating_prompt("story_rating")

        system_prompt = """אתה עורך ומבקר ספרים מנוסה המתמחה בספרות ילדים.
העריך את הסיפור לפי איכות הכתיבה, המסר החינוכי, והתאמה לגיל היעד.
היה ביקורתי ודרוש רמה גבוהה."""

        # Build story text for evaluation
        story_text = f"כותרת: {story['title']}\n\n"
        for page in story['pages']:
            story_text += f"--- עמוד {page['page_number']} ---\n"
            story_text += f"{page['text']}\n"
            story_text += f"[תיאור ויזואלי: {page['visual_description']}]\n\n"

        user_prompt = f"""העריך את הסיפור הבא:

{story_text}

נושא מקורי: {topic['name']}
ערך חינוכי מיועד: {topic['educational_value']}

{rating_prompt}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        rating_data = json.loads(response.choices[0].message.content)

        return {
            "story": story,
            "rating": rating_data,
            "approved": self.rating_system.meets_threshold(
                rating_data["weighted_score"],
                "story_rating"
            )
        }

    def rate_characters(self, characters: List[Dict]) -> List[Dict]:
        """
        מעריך דמויות
        """
        rating_prompt = self.rating_system.get_rating_prompt("character_rating")

        results = []
        for character in characters:
            system_prompt = """אתה מומחה לפיתוח דמויות בספרות ילדים.
העריך את הדמות לפי פוטנציאל הזיהוי, הייחודיות והמשיכה הויזואלית."""

            user_prompt = f"""העריך את הדמות הבאה:

שם: {character['name']}
תיאור פיזי: {character['physical_description']}
אופי: {character['personality']}
רקע: {character['background']}
ייחודיות: {character['unique_trait']}

{rating_prompt}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            rating_data = json.loads(response.choices[0].message.content)

            results.append({
                "character": character,
                "rating": rating_data,
                "approved": self.rating_system.meets_threshold(
                    rating_data["weighted_score"],
                    "character_rating"
                )
            })

        return results


# Test
if __name__ == "__main__":
    agent = OpenAIAgent()
    print("Testing OpenAI Agent...")

    test_topic = {
        "id": 1,
        "name": "הלילה הראשון בלי חיתול",
        "sub_topics": ["פחד מכישלון", "גאווה עצמית", "תמיכה הורית"],
        "educational_value": "התמודדות עם שינוי והתפתחות עצמאות",
        "story_concept": "ילד/ה שמפחדים מהמעבר לישון בלי חיתול"
    }

    result = agent.rate_topics([test_topic])
    print(json.dumps(result, ensure_ascii=False, indent=2))
