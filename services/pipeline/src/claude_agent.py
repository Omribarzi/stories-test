"""
Claude Agent - אחראי על יזימת תוכן ויצירה
"""
import os
import json
from anthropic import Anthropic
from typing import Dict, List, Optional
from dotenv import load_dotenv
from story_style_guidelines import get_style_prompt_for_age, get_age_params

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
                    existing_feedback: str = None,
                    existing_story: Dict = None,
                    age: int = 5,
                    num_pages: int = 10) -> Dict:
        """
        יוצר סיפור מלא על בסיס נושא, דמות וסגנון

        Args:
            topic: פרטי הנושא
            character: פרטי הדמות הראשית
            style_guide: מדריך הסגנון
            existing_feedback: משוב מהאיטרציה הקודמת
            existing_story: הסיפור הקיים לעריכה (כאשר יש feedback)
            age: גיל יעד (ברירת מחדל 5)
        """
        age_params = get_age_params(age)

        system_prompt = f"""אתה סופר מוכשר של ספרי ילדים בעברית.
תפקידך לכתוב סיפורים מרתקים, חינוכיים ומתאימים לגיל {age}.
הטון: חם, מרגיע, מתאים לשעת שינה.

=== כללי מבנה (חובה) ===
- משפטים קצרים: עד {age_params['max_words_per_sentence']} מילים למשפט.
- {age_params['sentences_per_page']} משפטים בכל עמוד, {age_params['words_per_page']} מילים לעמוד.
- מבנה סיפורי: התחלה (הצגת עולם + דמות), קונפליקט, שיא, פתרון.
- סיום חזק: העמוד האחרון נגמר במשפט שלם עם נקודה/סימן קריאה/שאלה.
- כל עמוד כולל visual_description מפורט — מה מופיע בציור, צבעים, הבעות פנים, מצב רוח.

=== כללי איכות (חובה) ===

1. Show, Don't Tell — הראה, אל תסביר
   ❌ "ליאור הבין שמשחק הוגן הוא חשוב"
   ✅ "ליאור הסתכל על החברים שצוחקים ביחד, והרגיש פתאום קל יותר"

2. דיאלוגים טבעיים — ילדים מדברים כמו ילדים
   ❌ "זה בסדר לטעות, אבל צריך לשחק לפי החוקים"
   ✅ "אה, קצת רימית... זה לא כיף ככה"

3. מורכבות רגשית — רגשות לא שחור-לבן
   ❌ "ליאור הרגיש שמח"
   ✅ "ליאור רצה לצעוק משמחה, אבל גם הרגיש משהו מצמרר בבטן"

4. פרטים חושיים וקונקרטיים — צבעים, קולות, ריחות, תנועות
   ❌ "הם שיחקו במשחק"
   ✅ "הקוביה קפצה על הדשא והתגלגלה עד שעצרה על 6"

5. אפס מסרים מפורשים — תן לקורא להסיק בעצמו
   ❌ "הוא למד שחברות חשובה מניצחון"
   ✅ "ליאור ראה את עומר מנסה לעשות בועות מהמים וצחק. מי צריך אוצר?"

6. קונפליקטים אמיתיים — לא פתרונות מהירים
   ❌ "סליחה!" ואז הכל מושלם
   ✅ אי נוחות, שקט מביך, ואז לאט לאט דברים משתפרים

7. דמויות עם עומק — פעולות ותנועות, לא הרהורים
   ❌ "ליאור חשב על היום. הוא הבין ש..."
   ✅ "ליאור בעט בחצץ בדרך לכיתה. קפץ פעמיים על רגל אחת"

8. רגע אמת — רגע אחד שבו הדמות מחליטה לבד, מחוויה, לא מהסבר. לפני הפעולה המשמעותית, תאר את הקושי הפיזי או ההיסוס (ידיים רועדות, פה יבש, לב דופק) — זה מה שהופך את הרגע לאמין
9. התנהגות אמיתית — בכל סיפור על רגש, הוסף רגע שבו הילד מתנהג פחות יפה בגלל הרגש (צועק, דוחף, מתעלם, בורח). רק אחרי זה אפשר לו לתקן — לא מיד, בהדרגה.
10. סיום שקט — לא מלמד מוסר, לא מסכם, משאיר מקום לפרשנות
11. סתירה פנימית — תן לכל דמות תכונה דומיננטית + תכונה אחת שסותרת אותה. ה"ספורטאי" שמודה שהוא גרוע, ה"שקטה" שפתאום צועקת הכי חזק. הפער הזה הופך ניצב לדמות.
12. Voice — לכל דמות הרגל לשוני אחד: אחד מדבר קצר ("בואי", "יאללה"), אחת שואלת שאלות, אחד תמיד מוסיף פרט לא קשור. הקורא צריך לזהות מי מדבר בלי "אמר/אמרה".
13. הומור פיזי — כישלונות חינניים: נעל שעפה עם הכדור, כיסא שנפל, שתייה שנשפכה על האף. ילדים צוחקים כשדברים קורים לגוף, לא כשמישהו אומר בדיחה.
14. דיאלוג עם פעולה — במקום "אמרה נועה", כתוב מה הדמות עושה תוך כדי דיבור: "נועה משכה את הרוכסן של התיק. 'אני לא באה.'". הגוף ממשיך לפעול גם כשהפה מדבר.

=== חוק הזהב (הכי חשוב!) ===

1. אם אפשר לאחד שני עמודים בלי לפגוע ברגש — חובה לאחד. אל תמלא עמודים. כל עמוד חייב להצדיק את קיומו.

2. חייב להיות חיכוך אחד לא יפה — רגע שבו הדמות מתנהגת רע (צועקת, דוחפת, מתעלמת, בורחת, שוברת, משקרת). בלי חיכוך כזה הסיפור בטוח מדי ולא אמיתי. זה הרגע שילד מזהה את עצמו.

3. רגש נבנה מפעולה, לא מהסבר. אם אפשר למחוק משפט רגשי ועדיין להבין את הרגש דרך מה שקורה — מחק אותו. הסיפור תמיד ייצא טוב יותר.

=== מה אסור בשום מצב ===
- "הבין ש...", "למד ש...", "המסר הוא...", "ולמדו שיעור חשוב"
- הורה/מבוגר שצופה בשקט מהצד ומחייך
- סיום שמסביר מה הדמות למדה
- חיזוקים חיצוניים מוגזמים ("איזה גיבור!", "אני כל כך גאה!")"""

        # Inject age-specific style rules
        age_style = get_style_prompt_for_age(age)
        system_prompt += f"\n\n=== כללים ספציפיים לגיל {age} ===\n{age_style}"

        # If we have an existing story + feedback, use EDIT mode (not full rewrite)
        if existing_feedback and existing_story:
            existing_pages_text = ""
            for page in existing_story.get('pages', []):
                existing_pages_text += f"עמוד {page['page_number']}:\n{page['text']}\n\n"

            user_prompt = f"""הנה סיפור קיים שצריך עריכה ממוקדת (לא כתיבה מחדש!).

כותרת נוכחית: {existing_story.get('title', '')}

הסיפור הנוכחי:
{existing_pages_text}

משוב מהמעריך:
{existing_feedback}

הוראות חשובות:
1. תקן רק את הנקודות שהמעריך ציין
2. שמור על העלילה, הדמויות, והמבנה הקיים
3. אל תכתוב סיפור חדש — רק ערוך את הקיים
4. שמור על אותו מספר עמודים
5. שמור על תיאורים ויזואליים דומים

דמות ראשית: {character['name']}
גיל יעד: 5-8

השב בפורמט JSON:
{{
    "title": "שם הספר",
    "pages": [
        {{
            "page_number": 1,
            "text": "הטקסט בעמוד",
            "visual_description": "תיאור מפורט של הציור בעמוד - מה יופיע, צבעים, מצב רוח"
        }}
    ],
    "summary": "תקציר הסיפור",
    "educational_notes": "הערות להורים על השימוש החינוכי בספר"
}}
"""
        else:
            user_prompt = f"""צור סיפור של {num_pages} עמודים בדיוק.

נושא: {topic['name']}
תת-נושאים: {', '.join(topic['sub_topics'])}
ערך חינוכי: {topic['educational_value']}

דמות ראשית: {character['name']}
תיאור: {character.get('description', character.get('physical_description', ''))}

מדריך סגנון:
- טון: {style_guide.get('tone', 'חם ומזמין')}
- אורך כל עמוד: {style_guide.get('words_per_page', '40-60')} מילים
- סגנון עיצובי: {style_guide.get('visual_style', 'צבעוני ומלא חיים')}

השב בפורמט JSON:
{{
    "title": "שם הספר",
    "pages": [
        {{
            "page_number": 1,
            "text": "הטקסט בעמוד",
            "visual_description": "תיאור מפורט של הציור בעמוד - מה יופיע, צבעים, מצב רוח"
        }}
    ],
    "summary": "תקציר הסיפור",
    "educational_notes": "הערות להורים על השימוש החינוכי בספר"
}}
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
