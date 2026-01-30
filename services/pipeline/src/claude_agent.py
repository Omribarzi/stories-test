"""
Claude Agent - אחראי על יזימת תוכן ויצירה
"""
import os
import json
from anthropic import Anthropic
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class ClaudeAgent:
    def __init__(self, model: str = None):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

    def generate_topics(self, num_topics: int = 100, existing_feedback: str = None) -> Dict:
        """
        מייצר הצעות לנושאי ספרים

        Args:
            num_topics: מספר נושאים לייצר
            existing_feedback: משוב מ-OpenAI על הצעה קודמת
        """
        system_prompt = """אתה מומחה לספרות ילדים וחינוך גיל הרך.
תפקידך להציע נושאים לספרי ילדים איכותיים לגילאי 5-8.
כל נושא צריך להיות:
- רלוונטי לחיי היומיום של ילדים ישראלים
- בעל ערך חינוכי ברור
- מעניין ומרתק לקריאה
- ניתן ליישום בסיפור של 12-15 עמודים

כל נושא יכלול:
- שם הנושא
- תת-נושאים ספציפיים (2-4)
- הערך החינוכי המרכזי
- רעיון ראשוני לעלילה"""

        user_prompt = f"הצע {num_topics} נושאים לספרי ילדים חינוכיים לגילאי 5-8.\n\n"

        if existing_feedback:
            user_prompt += f"התחשב במשוב הבא מהמעריך:\n{existing_feedback}\n\n"

        user_prompt += """
נושאים לדוגמה שכדאי להתייחס אליהם:
- שגרות יומיומיות: שינה, התארגנות בבוקר, צחצוח שיניים
- חברה וחברות: שיתוף, פתרון קונפליקטים, אמפתיה
- רגשות: כעס, פחד, עצב, שמחה, קנאה
- אתגרים: התחלה בחוג חדש, לילה ראשון בלי חיתול, ויתור על מוצץ
- בריאות: תזונה בריאה, ספורט, היגיינה
- משפחה: אח/ות חדשים, גירושים, אובדן
- למידה: סקרנות, התמדה, טעויות כחלק מהצמיחה
- חינוך מיני מותאם לגיל
- מסכים וטכנולוגיה

השב בפורמט JSON:
{
    "topics": [
        {
            "id": 1,
            "name": "שם הנושא",
            "sub_topics": ["תת-נושא 1", "תת-נושא 2"],
            "educational_value": "הערך החינוכי",
            "story_concept": "רעיון ראשוני לעלילה"
        }
    ]
}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            temperature=1.0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Extract JSON from response
        content = response.content[0].text
        # Try to find JSON in the response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("Could not parse JSON from Claude response")

    def create_story(self, topic: Dict, character: Dict, style_guide: Dict,
                    existing_feedback: str = None) -> Dict:
        """
        יוצר סיפור מלא על בסיס נושא, דמות וסגנון

        Args:
            topic: פרטי הנושא
            character: פרטי הדמות הראשית
            style_guide: מדריך הסגנון
            existing_feedback: משוב מהאיטרציה הקודמת
        """
        system_prompt = """אתה סופר מוכשר של ספרי ילדים בעברית.
תפקידך לכתוב סיפורים מרתקים, חינוכיים ומתאימים לגילאי 5-8.

עקרונות כתיבה:
- שפה עשירה אך מובנת לילדים
- עלילה דינמית עם התחלה, אמצע וסוף
- המסר החינוכי משולב באופן טבעי, לא מטיף
- דיאלוגים חיים ואותנטיים
- תיאורים ויזואליים שמתאימים לאיור"""

        user_prompt = f"""צור סיפור של 12-15 עמודים.

נושא: {topic['name']}
תת-נושאים: {', '.join(topic['sub_topics'])}
ערך חינוכי: {topic['educational_value']}

דמות ראשית: {character['name']}
תיאור: {character.get('description', character.get('physical_description', ''))}

מדריך סגנון:
- טון: {style_guide.get('tone', 'חם ומזמין')}
- אורך כל עמוד: {style_guide.get('words_per_page', '40-60')} מילים
- סגנון עיצובי: {style_guide.get('visual_style', 'צבעוני ומלא חיים')}

"""

        if existing_feedback:
            user_prompt += f"\nמשוב מהאיטרציה הקודמת:\n{existing_feedback}\n\n"

        user_prompt += """
השב בפורמט JSON:
{
    "title": "שם הספר",
    "pages": [
        {
            "page_number": 1,
            "text": "הטקסט בעמוד",
            "visual_description": "תיאור מפורט של הציור בעמוד - מה יופיע, צבעים, מצב רוח"
        }
    ],
    "summary": "תקציר הסיפור",
    "educational_notes": "הערות להורים על השימוש החינוכי בספר"
}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            temperature=0.9,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        content = response.content[0].text
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("Could not parse JSON from Claude response")

    def propose_characters(self, num_characters: int = 10,
                          existing_feedback: str = None) -> Dict:
        """
        מציע דמויות לסיפורים
        """
        system_prompt = """אתה מעצב דמויות מקורי לספרי ילדים.
צור דמויות שילדים ישראלים יכולים להזדהות איתן.
הדמויות צריכות להיות ייחודיות, מעניינות ומגוונות."""

        user_prompt = f"הצע {num_characters} דמויות לסדרת ספרי ילדים.\n\n"

        if existing_feedback:
            user_prompt += f"משוב:\n{existing_feedback}\n\n"

        user_prompt += """
כל דמות תכלול:
- שם
- תיאור פיזי
- תכונות אופי
- רקע
- מה הופך אותה למיוחדת

השב בפורמט JSON:
{
    "characters": [
        {
            "name": "שם הדמות",
            "physical_description": "תיאור פיזי מפורט",
            "personality": "תכונות אופי",
            "background": "רקע",
            "unique_trait": "מה מיוחד בדמות"
        }
    ]
}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            temperature=1.0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        content = response.content[0].text
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("Could not parse JSON from Claude response")


# Test
if __name__ == "__main__":
    agent = ClaudeAgent()
    print("Testing Claude Agent...")
    topics = agent.generate_topics(num_topics=5)
    print(json.dumps(topics, ensure_ascii=False, indent=2))
