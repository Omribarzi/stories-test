#!/usr/bin/env python3
"""
Story Personalizer Smart - שימוש ב-Claude להחלפה חכמה
"""
import json
from pathlib import Path
from typing import Dict
from claude_agent import ClaudeAgent


class StoryPersonalizerSmart:
    """
    מתאים סיפור בצורה חכמה עם Claude
    """

    def __init__(self):
        self.claude = ClaudeAgent()
        self.client = self.claude.client
        self.model = self.claude.model
    
    def personalize_story(self, story_data: Dict,
                         child_name: str,
                         child_gender: str,
                         mother_name: str = None,
                         father_name: str = None) -> Dict:
        """
        מתאים סיפור בצורה חכמה
        """
        import copy
        personalized = copy.deepcopy(story_data)
        
        original_name = personalized['character']['name']
        personalized['character']['name'] = child_name
        
        # עדכן כותרת
        if child_gender == "boy":
            personalized['story']['title'] = f"הלילה הגדול של {child_name}"
        else:
            personalized['story']['title'] = f"הלילה הגדול של {child_name}"
        
        print(f"✨ מתאים סיפור ל-{child_name} (בצורה חכמה)...")
        
        # עבור על כל עמוד
        for i, page in enumerate(personalized['story']['pages']):
            print(f"   עמוד {i+1}...", end='', flush=True)
            
            # השתמש ב-Claude לתרגום חכם
            page['text'] = self._adapt_text_smart(
                page['text'],
                original_name,
                child_name,
                child_gender,
                mother_name,
                father_name
            )
            
            page['visual_description'] = self._adapt_text_smart(
                page['visual_description'],
                original_name,
                child_name,
                child_gender,
                mother_name,
                father_name
            )
            
            print(" ✓")
        
        # עדכן summary
        personalized['story']['summary'] = self._adapt_text_smart(
            personalized['story']['summary'],
            original_name,
            child_name,
            child_gender,
            mother_name,
            father_name
        )
        
        return personalized
    
    def _adapt_text_smart(self, text: str, 
                         original_name: str, 
                         new_name: str,
                         gender: str,
                         mother_name: str = None,
                         father_name: str = None) -> str:
        """
        משתמש ב-Claude להתאמה חכמה של הטקסט
        """
        gender_he = "זכר" if gender == "boy" else "נקבה"
        
        prompt = f"""התאם את הטקסט הבא לשם חדש ומגדר חדש.

שינויים:
1. החלף את השם "{original_name}" ל-"{new_name}"
2. התאם את כל הפעלים, שמות התואר והכינויים למגדר {gender_he}
"""
        
        if mother_name and mother_name != "אמא":
            prompt += f'''3. החלף "אמא" ב-"אמא {mother_name}" -
   - כתוב תמיד "אמא {mother_name}" (עם המילה "אמא" לפני השם)
   - אמא {mother_name} היא נקבה, השתמש בצורות פועל בלשון נקבה (למשל: חיבקה, אמרה, הלכה)
   - דוגמאות: "אמא {mother_name} חיבקה אותו", "אמא {mother_name} ישבה לידו"\n'''

        if father_name and father_name != "אבא":
            prompt += f'''4. החלף "אבא" ב-"אבא {father_name}" -
   - כתוב תמיד "אבא {father_name}" (עם המילה "אבא" לפני השם)
   - אבא {father_name} הוא זכר, השתמש בצורות פועל בלשון זכר (למשל: חיבק, אמר, הלך)
   - דוגמאות: "אבא {father_name} הרים אגודל", "אבא {father_name} עמד מאחור"\n'''
        
        prompt += f"""
טקסט מקורי:
{text}

החזר את הטקסט המותאם בלבד, ללא הסברים."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return response.content[0].text.strip()


if __name__ == "__main__":
    print("✅ Smart Story Personalizer מוכן")
