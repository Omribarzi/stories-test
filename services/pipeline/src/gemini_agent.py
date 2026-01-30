"""
Gemini Agent - אחראי על יצירת ויזואלים
"""
import os
import json
from typing import Dict, List
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class GeminiAgent:
    def __init__(self, model: str = None):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.model = genai.GenerativeModel(self.model_name)

    def enhance_visual_descriptions(self, story: Dict, style_guide: Dict) -> Dict:
        """
        משפר תיאורים ויזואליים לשימוש ב-Imagen/Nanobana

        Args:
            story: הסיפור עם תיאורים ראשוניים
            style_guide: מדריך סגנון עיצובי

        Returns:
            סיפור עם תיאורים ויזואליים משופרים
        """
        system_instruction = """אתה מומחה לתיאור ויזואלי לצורך יצירת איורים ב-AI.
תפקידך לקחת תיאור כללי ולהפוך אותו לפרומפט מפורט ומדויק ליצירת תמונה.

עקרונות:
- תאר בדיוק מה יופיע בתמונה
- כלול פרטים על צבעים, תאורה, זווית צילום
- ציין את סגנון האיור (קריקטורי, ריאליסטי, מינימליסטי)
- וודא עקביות בין עמודים (דמויות, סגנון, סביבה)
- התאם לגילאי 5-8 - צבעוני, ידידותי, לא מפחיד"""

        enhanced_story = story.copy()
        enhanced_story['pages'] = []

        for page in story['pages']:
            prompt = f"""שפר את התיאור הויזואלי הבא לפרומפט ליצירת איור:

כותרת הספר: {story['title']}
עמוד: {page['page_number']}
טקסט: {page['text']}
תיאור ויזואלי ראשוני: {page['visual_description']}

מדריך סגנון:
- סגנון: {style_guide.get('visual_style', 'קריקטורי צבעוני')}
- מצב רוח: {style_guide.get('mood', 'חם ומזמין')}
- קהל יעד: ילדים בגילאי 5-8

צור פרומפט מפורט ליצירת האיור. הפרומפט צריך להיות באנגלית.
כלול:
1. תיאור הסצנה הראשית
2. פרטים על הדמויות (מראה, ביטוי פנים, תנוחה)
3. סביבה ורקע
4. צבעים ותאורה
5. סגנון אמנותי
6. מצב רוח ואווירה

השב בפורמט JSON:
{{
    "hebrew_description": "תיאור מפורט בעברית",
    "english_prompt": "Detailed prompt in English for image generation",
    "style_tags": ["tag1", "tag2"],
    "technical_specs": {{
        "aspect_ratio": "recommended ratio",
        "style": "art style",
        "mood": "overall mood"
    }}
}}
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )

            enhanced_visual = json.loads(response.text)

            enhanced_page = page.copy()
            enhanced_page['visual_description_enhanced'] = enhanced_visual['hebrew_description']
            enhanced_page['image_prompt'] = enhanced_visual['english_prompt']
            enhanced_page['style_tags'] = enhanced_visual['style_tags']
            enhanced_page['technical_specs'] = enhanced_visual['technical_specs']

            enhanced_story['pages'].append(enhanced_page)

        return enhanced_story

    def generate_style_consistency_guide(self, story_title: str,
                                        initial_visual_concept: str) -> Dict:
        """
        יוצר מדריך עקביות ויזואלית לכל הספר
        """
        prompt = f"""צור מדריך עקביות ויזואלית לספר ילדים:

שם הספר: {story_title}
קונצפט ויזואלי: {initial_visual_concept}

המדריך צריך לכלול:
1. פלטת צבעים (5-7 צבעים עיקריים)
2. סגנון אמנותי מדויק
3. מאפייני הדמויות הקבועים
4. סגנון רקעים
5. טיפוגרפיה מומלצת

השב בפורמט JSON:
{{
    "color_palette": ["#hex1", "#hex2"],
    "art_style": "detailed description",
    "character_consistency": {{
        "main_character": "consistent features",
        "supporting_characters": "consistent features"
    }},
    "background_style": "description",
    "typography": "font suggestions",
    "mood": "overall mood and feel"
}}
"""

        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.5,
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)

    def prepare_for_nanobana(self, enhanced_story: Dict) -> List[Dict]:
        """
        מכין את התיאורים לשימוש ב-Nanobana או Imagen

        Returns:
            רשימת פרומפטים מוכנים לשימוש
        """
        nanobana_prompts = []

        for page in enhanced_story['pages']:
            prompt_data = {
                "page_number": page['page_number'],
                "prompt": page['image_prompt'],
                "negative_prompt": "scary, violent, inappropriate for children, dark, horror",
                "style_preset": page['technical_specs'].get('style', 'children-book-illustration'),
                "aspect_ratio": page['technical_specs'].get('aspect_ratio', '4:3'),
                "quality": "high",
                "metadata": {
                    "book_title": enhanced_story['title'],
                    "page_text": page['text'],
                    "style_tags": page['style_tags']
                }
            }
            nanobana_prompts.append(prompt_data)

        return nanobana_prompts


# Test
if __name__ == "__main__":
    agent = GeminiAgent()
    print("Testing Gemini Agent...")

    test_story = {
        "title": "הלילה הראשון בלי חיתול",
        "pages": [
            {
                "page_number": 1,
                "text": "נועה בת חמש התרגשה מאוד. הערב, בפעם הראשונה, היא תישן בלי חיתול!",
                "visual_description": "ילדה מחייכת עומדת ליד מיטתה, עם פיג'מה צבעונית"
            }
        ]
    }

    style_guide = {
        "visual_style": "קריקטורי צבעוני ועדין",
        "mood": "חם ומעודד"
    }

    enhanced = agent.enhance_visual_descriptions(test_story, style_guide)
    print(json.dumps(enhanced, ensure_ascii=False, indent=2))
