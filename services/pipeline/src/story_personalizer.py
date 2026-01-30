#!/usr/bin/env python3
"""
Story Personalizer - התאמה אישית של סיפורים
"""
import json
from pathlib import Path
from typing import Dict
import re


class StoryPersonalizer:
    """
    מתאים סיפור לילד ספציפי - שמות, מגדרים, פרטים משפחתיים
    """
    
    def __init__(self):
        pass
    
    def personalize_story(self, story_data: Dict, 
                         child_name: str,
                         child_gender: str,  # "boy" or "girl"
                         mother_name: str = None,
                         father_name: str = None) -> Dict:
        """
        מתאים סיפור קיים לילד ספציפי
        
        Args:
            story_data: נתוני הסיפור המקוריים
            child_name: שם הילד החדש
            child_gender: "boy" או "girl"
            mother_name: שם האמא (אופציונלי)
            father_name: שם האבא (אופציונלי)
        
        Returns:
            story_data מותאם אישית
        """
        print(f"✨ מתאים סיפור ל-{child_name}...")
        
        # הגדרות מגדר - פעלים ושמות תואר בלשון נקבה -> זכר
        if child_gender == "boy":
            pronouns = {
                # כינויים
                "היא": "הוא",
                "שלה": "שלו",
                "אותה": "אותו",
                "לה": "לו",
                "ילדה": "ילד",
                "בת": "בן",
                "הגיבורה": "הגיבור",
                # שמות תואר
                "מוכנה": "מוכן",
                "גדולה": "גדול",
                "אמיצה": "אמיץ",
                "מודאגות": "מודאגים",
                "נחושות": "נחושים",
                "גאה": "גאה",  # זה זהה
                # פעלים - עבר
                "עמדה": "עמד",
                "הביטה": "הביט",
                "ליטפה": "ליטף",
                "הרגישה": "הרגיש",
                "ניסתה": "ניסה",
                "זכרה": "זכר",
                "התעוררה": "התעורר",
                "ירדה": "ירד",
                "נגעו": "נגעו",  # זה זהה לזכר
                "עשתה": "עשה",
                "קפאה": "קפא",
                "ראתה": "ראה",
                "צחקה": "צחק",
                "לחשה": "לחש",
                "התכרבלה": "התכרבל",
                "נזכרה": "נזכר",
                "מיהרה": "מיהר",
                "קיבלה": "קיבל",
                "אמרה": "אמר",
                "חשבה": "חשב",
                "שאלה": "שאל",
                "ידעה": "ידע",
                "התכוננה": "התכונן",
                "חיכתה": "חיכה",
                "שכבה": "שכב",
                "סגרה": "סגר",
                "פתחה": "פתח",
                "עלתה": "עלה",
                "השתמשה": "השתמש",
                "שטפה": "שטף",
                "עצרה": "עצר",
                "הסתכלה": "הסתכל",
                "חזרה": "חזר",
                "קפצה": "קפץ",
                "סיפרה": "סיפר",
                "נראית": "נראה",
                "לבושה": "לבוש",
                "נראית": "נראה",
                # פעלים - הווה
                "צריכה": "צריך",
                "יכולה": "יכול",
                "מתרגשת": "מתרגש"
            }
        else:
            pronouns = {}  # אם זה בת, הסיפור המקורי כבר נכון
        
        # העתק story_data
        import copy
        personalized_story = copy.deepcopy(story_data)
        
        # שנה שם הילד
        original_name = personalized_story['character']['name']
        personalized_story['character']['name'] = child_name
        
        # עדכן כותרת
        original_title = personalized_story['story']['title']
        if child_gender == "boy":
            new_title = original_title.replace("של נועה", f"של {child_name}")
            new_title = new_title.replace("הגדול", "הגדול")  # זה נשאר
        else:
            new_title = original_title.replace("נועה", child_name)
        personalized_story['story']['title'] = new_title
        
        # עבור על כל עמודי הסיפור
        for page in personalized_story['story']['pages']:
            # החלף את השם
            page['text'] = page['text'].replace(original_name, child_name)
            page['visual_description'] = page['visual_description'].replace(original_name, child_name)
            
            # החלף כינויים (רק אם בן)
            if child_gender == "boy":
                for fem, masc in pronouns.items():
                    # החלף בטקסט
                    page['text'] = self._smart_replace(page['text'], fem, masc)
                    # החלף בתיאור ויזואלי
                    page['visual_description'] = self._smart_replace(
                        page['visual_description'], fem, masc
                    )
        
        # שנה שמות הורים אם צוין
        if mother_name:
            personalized_story['story']['pages'] = [
                {**page, 
                 'text': page['text'].replace('אמא', mother_name),
                 'visual_description': page['visual_description'].replace('אמא', mother_name if 'אמא' in page['visual_description'] else page['visual_description'])}
                for page in personalized_story['story']['pages']
            ]
        
        if father_name:
            personalized_story['story']['pages'] = [
                {**page,
                 'text': page['text'].replace('אבא', father_name),
                 'visual_description': page['visual_description'].replace('אבא', father_name if 'אבא' in page['visual_description'] else page['visual_description'])}
                for page in personalized_story['story']['pages']
            ]
        
        # עדכן summary
        summary = personalized_story['story']['summary']
        summary = summary.replace(original_name, child_name)
        if child_gender == "boy":
            for fem, masc in pronouns.items():
                summary = self._smart_replace(summary, fem, masc)
        personalized_story['story']['summary'] = summary
        
        return personalized_story
    
    def _smart_replace(self, text: str, old: str, new: str) -> str:
        """
        החלפה חכמה שמתחשבת בגבולות מילים
        """
        # החלף רק במילים שלמות
        pattern = r'\b' + re.escape(old) + r'\b'
        return re.sub(pattern, new, text)


# Test
if __name__ == "__main__":
    personalizer = StoryPersonalizer()
    
    # טען סיפור לדוגמה
    story_file = Path("../data/stories/story_20260127_185923.json")
    if story_file.exists():
        with open(story_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        # התאם לאדם
        personalized = personalizer.personalize_story(
            story_data,
            child_name="אדם",
            child_gender="boy",
            mother_name="אור",
            father_name="עמרי"
        )
        
        print("\n✅ דוגמה להתאמה:")
        print(f"   כותרת מקורית: {story_data['story']['title']}")
        print(f"   כותרת חדשה: {personalized['story']['title']}")
        print(f"\n   עמוד 1 מקורי: {story_data['story']['pages'][0]['text'][:80]}...")
        print(f"   עמוד 1 חדש: {personalized['story']['pages'][0]['text'][:80]}...")
    else:
        print("✅ Story Personalizer מוכן לשימוש")
