#!/usr/bin/env python3
"""
Character Analyzer - ניתוח תמונות של ילדים ויצירת תיאור לאילוסטרציה
"""
import base64
from pathlib import Path
from typing import List, Dict
import anthropic
import os


class CharacterAnalyzer:
    """
    מנתח תמונות של ילד ויוצר תיאור מפורט לאילוסטרציה
    """
    
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    def analyze_character_from_images(self, image_paths: List[Path], 
                                     child_name: str,
                                     age: int,
                                     gender: str = "boy") -> Dict:
        """
        מנתח תמונות של ילד ויוצר תיאור מפורט לאילוסטרציה
        
        Args:
            image_paths: רשימת נתיבים לתמונות
            child_name: שם הילד
            age: גיל הילד
            gender: "boy" או "girl"
        
        Returns:
            Dict עם תיאור מפורט של הדמות
        """
        print(f"🔍 מנתח תמונות של {child_name}...")
        
        # קרא והמר תמונות ל-base64
        image_contents = []
        for img_path in image_paths[:3]:  # מקסימום 3 תמונות
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    image_data = base64.standard_b64encode(f.read()).decode("utf-8")
                    image_contents.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        }
                    })
        
        if not image_contents:
            raise ValueError("לא נמצאו תמונות תקינות")
        
        # בנה prompt לניתוח
        gender_he = "ילד" if gender == "boy" else "ילדה"
        pronoun = "הוא" if gender == "boy" else "היא"
        
        prompt = f"""אתה מומחה בניתוח תמונות ויצירת תיאורים לאילוסטרציות ספרי ילדים.

נתונים:
- שם: {child_name}
- גיל: {age}
- מגדר: {gender_he}

משימה: נתח את התמונות ויצור תיאור מפורט של {child_name} לשימוש באילוסטרציות.

התמקד ב:
1. **מראה פיזי:**
   - צבע ומרקם שיער (ישר/מתולתל/גלי, קצר/ארוך)
   - צבע עיניים
   - גוון עור
   - מבנה פנים (עגול/מוארך, לחיים, אף, פה)
   - גובה ומבנה גוף (רזה/חסון/ממוצע)

2. **מאפיינים ייחודיים:**
   - צורת פנים
   - חיוך (שיניים, פה)
   - תווי פנים בולטים
   - סגנון או אלמנטים ייחודיים

3. **סגנון אילוסטרציה:**
   - איך לתאר את {child_name} באילוסטרציה של ספר ילדים
   - מה הופך את {pronoun} לייחודי ומזהה

תן תשובה בפורמט JSON:
{{
    "physical_description": "תיאור פיזי מפורט בעברית",
    "english_prompt_description": "Detailed physical description in English for AI image generation - include hair (color, texture, length), eyes (color, shape), skin tone, face shape, body build, age-appropriate features",
    "unique_features": ["מאפיין 1", "מאפיין 2", "מאפיין 3"],
    "illustration_style_notes": "הערות לסגנון האילוסטרציה",
    "personality_impression": "רושם אישיות מהתמונות (אנרגטי/שקט/מצחיק וכו')"
}}"""
        
        # שלח ל-Claude Vision
        content = [{"type": "text", "text": prompt}] + image_contents
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        
        # Parse JSON
        import json
        response_text = response.content[0].text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            character_data = json.loads(response_text[json_start:json_end])
            
            # הוסף מטא-דאטה
            character_data["name"] = child_name
            character_data["age"] = age
            character_data["gender"] = gender
            
            return character_data
        else:
            raise ValueError("Could not parse character analysis")


# Test
if __name__ == "__main__":
    analyzer = CharacterAnalyzer()
    
    # דוגמה - צריך להעביר נתיבים אמיתיים
    print("✅ Character Analyzer מוכן לשימוש")
    print("   השתמש ב-analyze_character_from_images() עם תמונות של הילד")
