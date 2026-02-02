"""
OpenAI Agent - אחראי על הערכה וביקורת
"""
import os
import json
import time
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

    @staticmethod
    def _strip_nikud(text: str) -> str:
        """Strip Hebrew nikud (vowel) characters to reduce token count."""
        import re
        return re.sub(r'[\u0591-\u05C7]', '', text)

    @staticmethod
    def _eval_header(age: int = 5) -> str:
        """Build eval context header dynamically per target age."""
        from story_style_guidelines import get_age_params
        params = get_age_params(age)
        return (
            "[הקשר הערכה]\n"
            f"גיל יעד: {age} | טון: חם, מרגיע, שעת שינה\n"
            f"פורמט: {params['pages']} עמודים, {params['sentences_per_page']} משפטים לעמוד, {params['words_per_page']} מילים\n"
            f"מקסימום מילים במשפט: {params['max_words_per_sentence']}\n"
            "מטרה: חיבור רגשי, הפחתת עומס הורי, מסר חינוכי טבעי\n"
            "אין לכלול: תיאורי איורים, metadata, JSON\n"
        )

    def rate_story(self, story: Dict, topic: Dict, eval_runs: int = 3, age: int = 5) -> Dict:
        """
        מעריך סיפור מלא.
        Runs eval_runs times (default 3) and returns the MEDIAN score.
        """
        rating_prompt = self.rating_system.get_rating_prompt("story_rating")

        system_prompt = """אתה עורך ומבקר ספרים מנוסה המתמחה בספרות ילדים.
העריך את הסיפור לפי איכות הכתיבה, המסר החינוכי, והתאמה לגיל היעד.
היה ביקורתי ודרוש רמה גבוהה."""

        # Build story text for evaluation — TEXT ONLY (no visual descriptions)
        story_text = f"כותרת: {story['title']}\n\n"
        for page in story['pages']:
            story_text += f"--- עמוד {page['page_number']} ---\n"
            story_text += f"{page['text']}\n\n"

        # Strip nikud to reduce tokens
        story_text = self._strip_nikud(story_text)

        # Cap length (deterministic truncation) — 6000 supports 19-page stories
        MAX_STORY_CHARS = 6000
        if len(story_text) > MAX_STORY_CHARS:
            story_text = story_text[:MAX_STORY_CHARS] + "\n[...קוצר...]"

        user_prompt = f"""{self._eval_header(age)}
העריך את הסיפור הבא:

{story_text}

נושא מקורי: {topic['name']}
ערך חינוכי מיועד: {topic['educational_value']}

{rating_prompt}
"""

        prompt_chars = len(user_prompt)
        print(f"      [MEDIAN_EVAL] input: {prompt_chars} chars, model={self.model}, runs={eval_runs}")

        # --- Median-of-N evaluation ---
        scores = []
        all_rating_data = []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        t0 = time.time()
        for run_idx in range(eval_runs):
            t_run = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            run_time = time.time() - t_run

            usage = response.usage
            if usage:
                total_prompt_tokens += usage.prompt_tokens
                total_completion_tokens += usage.completion_tokens

            rating_data = json.loads(response.choices[0].message.content)
            score = rating_data.get("weighted_score", 0)
            scores.append(score)
            all_rating_data.append(rating_data)
            print(f"      [MEDIAN_EVAL] run {run_idx+1}/{eval_runs}: score={score}, time={run_time:.1f}s")

        api_time = time.time() - t0

        # Pick median
        scores_sorted = sorted(scores)
        median_idx = len(scores_sorted) // 2
        median_score = scores_sorted[median_idx]
        # Use the rating_data that produced the median score
        median_data = all_rating_data[scores.index(median_score)]

        print(f"      [MEDIAN_EVAL] raw_scores={scores}, median={median_score}")
        print(f"      [MEDIAN_EVAL] total_tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}")
        print(f"      [MEDIAN_EVAL] total_api_time: {api_time:.1f}s")

        return {
            "story": story,
            "rating": median_data,
            "approved": self.rating_system.meets_threshold(
                median_data["weighted_score"],
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
