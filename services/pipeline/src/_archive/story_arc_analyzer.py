"""
Story Arc Analyzer - מנתח את מקום העמוד בקשת העלילה
ומתאים את ההנחיות הויזואליות בהתאם
"""
from typing import Dict, List


class StoryArcAnalyzer:
    """
    מנתח עמוד בהקשר של קשת העלילה ומספק הנחיות
    """

    def __init__(self, total_pages: int = 15):
        self.total_pages = total_pages

    def analyze_page_position(self, page_number: int, page_text: str,
                              all_pages: List[Dict] = None) -> Dict:
        """
        מנתח את מקום העמוד בסיפור ומחזיר הנחיות
        """
        # חלוקה לשלבי הסיפור
        third = self.total_pages / 3

        if page_number <= third:
            arc_stage = "setup"  # הקמה - צריך לשתול בעיה
        elif page_number <= third * 2:
            arc_stage = "conflict"  # קונפליקט - צריך מתח ואתגר
        else:
            arc_stage = "resolution"  # פתרון - יכול להיות חם יותר

        return {
            "arc_stage": arc_stage,
            "page_position": page_number / self.total_pages,
            "guidelines": self._get_guidelines(arc_stage, page_number, page_text)
        }

    def _get_guidelines(self, arc_stage: str, page_number: int,
                       page_text: str) -> Dict:
        """
        מחזיר הנחיות ויזואליות ספציפיות לשלב
        """
        if arc_stage == "setup":
            return {
                "emotional_intensity": "high",
                "story_purpose": "Hook the viewer, establish problem",
                "visual_priorities": [
                    "Show clear emotion (worry, fear, uncertainty)",
                    "Use visual elements dramatically (mirrors, shadows, light)",
                    "Body language should show the internal conflict",
                    "Include subtle visual hints of the problem",
                    "Create a question in the viewer's mind"
                ],
                "avoid": [
                    "Being too 'nice' or comfortable",
                    "Neutral expressions",
                    "Perfect, relaxed scenes",
                    "Just showing routine without tension"
                ],
                "mood_direction": "Introduce tension, create curiosity",
                "composition_notes": "Use composition to suggest inner turmoil or upcoming challenge"
            }

        elif arc_stage == "conflict":
            return {
                "emotional_intensity": "very high",
                "story_purpose": "Show struggle, challenge, growth",
                "visual_priorities": [
                    "Maximum dramatic tension",
                    "Strong body language showing effort or fear",
                    "Use lighting/shadows to enhance drama",
                    "Show the character facing the challenge",
                    "Visual metaphors for internal struggle"
                ],
                "avoid": [
                    "Resolving too quickly",
                    "Comfortable or safe feelings",
                    "Lack of visual tension"
                ],
                "mood_direction": "Peak emotional moment",
                "composition_notes": "Dynamic, showing action or inner battle"
            }

        else:  # resolution
            return {
                "emotional_intensity": "warm but earned",
                "story_purpose": "Show growth, resolution, but earned",
                "visual_priorities": [
                    "Warmth and connection, but not 'perfect'",
                    "Subtle hints that struggle was real",
                    "Pride, relief, accomplishment in expressions",
                    "Before/after visual callback if possible"
                ],
                "avoid": [
                    "Too saccharine or perfect",
                    "Forgetting the journey",
                    "Generic happy ending"
                ],
                "mood_direction": "Satisfying resolution with depth",
                "composition_notes": "Calm but with layers of earned emotion"
            }

    def detect_key_elements(self, page_text: str) -> Dict:
        """
        מזהה אלמנטים מפתח בטקסט שצריכים ביטוי ויזואלי
        """
        key_elements = {
            "emotions": [],
            "dramatic_elements": [],
            "internal_conflict": False,
            "action": False,
            "character_growth": False
        }

        # רגשות
        emotion_keywords = {
            "פחד": ["פחד", "מפחד", "פוחד", "חשש", "דאג"],
            "uncertainty": ["לא יודע", "אולי", "מה אם"],
            "determination": ["אני יכול", "נחישות", "החלט"],
            "relief": ["הקלה", "לבסוף", "הצליח"],
            "worry": ["דאגה", "מודאג", "חרד"]
        }

        for emotion, keywords in emotion_keywords.items():
            if any(kw in page_text for kw in keywords):
                key_elements["emotions"].append(emotion)

        # אלמנטים דרמטיים
        if "מראה" in page_text:
            key_elements["dramatic_elements"].append("mirror")

        if "חושך" in page_text or "צל" in page_text:
            key_elements["dramatic_elements"].append("shadows/darkness")

        if "לילה" in page_text or "ערב" in page_text:
            key_elements["dramatic_elements"].append("night/evening")

        # קונפליקט פנימי
        if any(phrase in page_text for phrase in ["מה אם", "לא יודע", "פחד", "מודאג"]):
            key_elements["internal_conflict"] = True

        # פעולה
        if any(word in page_text for word in ["הלכ", "רץ", "קפצ", "ירד"]):
            key_elements["action"] = True

        return key_elements

    def generate_visual_direction(self, page_number: int, page_text: str,
                                  total_pages: int = None) -> str:
        """
        יוצר הנחיות ויזואליות מפורטות בהתאם לניתוח
        """
        if total_pages:
            self.total_pages = total_pages

        analysis = self.analyze_page_position(page_number, page_text)
        elements = self.detect_key_elements(page_text)
        guidelines = analysis["guidelines"]

        direction = f"""
STORY POSITION: {analysis['arc_stage'].upper()} (page {page_number}/{self.total_pages})
PURPOSE: {guidelines['story_purpose']}
EMOTIONAL INTENSITY: {guidelines['emotional_intensity']}

VISUAL STORYTELLING PRIORITIES:
{chr(10).join(f'- {p}' for p in guidelines['visual_priorities'])}

DETECTED STORY ELEMENTS:
- Emotions to show: {', '.join(elements['emotions']) if elements['emotions'] else 'Subtle tension'}
- Dramatic elements: {', '.join(elements['dramatic_elements']) if elements['dramatic_elements'] else 'None specified'}
- Internal conflict: {'YES - must show in body language and expression' if elements['internal_conflict'] else 'No'}

MOOD DIRECTION: {guidelines['mood_direction']}

COMPOSITION: {guidelines['composition_notes']}

CRITICAL AVOIDS:
{chr(10).join(f'- {a}' for a in guidelines['avoid'])}
"""
        return direction.strip()


# Test
if __name__ == "__main__":
    analyzer = StoryArcAnalyzer(total_pages=15)

    # Test עמוד 1
    page1_text = 'נועה עמדה מול המראה בחדר האמבטיה, שיערה החום המתולתל קפץ לכל הכיוונים. היא הביטה בעיניים החומות הגדולות שלה וליטפה את פיג\'מת הכוכבים החדשה. "הלילה," אמרה בקול רציני, "אני כבר ילדה גדולה. בלי חיתולים!" הלב שלה דפק חזק. האם היא באמת מוכנה?'

    print("="*60)
    print("עמוד 1 - ניתוח")
    print("="*60)
    direction = analyzer.generate_visual_direction(1, page1_text, 15)
    print(direction)

    # Test עמוד 5
    page5_text = 'באמצע הלילה, נועה התעוררה. היה חשוך. היה שקט. והיא הרגישה... לחץ. הבטן שלה דיברה איתה. "אני צריכה לפיפי!" לחשה בבהלה. היא זכרה את המסדרון הארוך והחשוך עד לשירותים. זה נראה פתאום כמו מסע של גיבורה אמיתית.'

    print("\n" + "="*60)
    print("עמוד 5 - ניתוח")
    print("="*60)
    direction = analyzer.generate_visual_direction(5, page5_text, 15)
    print(direction)
