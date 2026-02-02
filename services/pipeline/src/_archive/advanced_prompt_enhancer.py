"""
Advanced Prompt Enhancer - משפר פרומפטים עם הבנה סיפורית
"""
from typing import Dict
from claude_agent import ClaudeAgent
from story_arc_analyzer import StoryArcAnalyzer


class AdvancedPromptEnhancer:
    """
    משפר פרומפטים עם הבנה של קשת העלילה וסיפוריות ויזואלית
    """

    def __init__(self):
        self.claude = ClaudeAgent()
        self.analyzer = StoryArcAnalyzer()

    def enhance_with_story_context(self, page_number: int, page_text: str,
                                   visual_description: str,
                                   character_description: str,
                                   total_pages: int = 15) -> Dict:
        """
        משפר פרומפט עם הבנה מלאה של הסיפוריות
        """
        # ניתוח מקום בסיפור
        story_direction = self.analyzer.generate_visual_direction(
            page_number, page_text, total_pages
        )

        # בניית פרומפט מתקדם
        prompt = f"""You are creating an illustration for a COMMERCIAL children's book that needs to SELL.

{story_direction}

PAGE CONTENT:
Text: {page_text}
Visual description: {visual_description}
Character: {character_description}

CRITICAL COMMERCIAL RULES:

1. EMOTIONAL IMPACT IS EVERYTHING
   - Every page must have clear, strong emotion
   - Parents and kids should FEEL something looking at this
   - Neutral/pleasant is NOT enough - we need connection

2. VISUAL STORYTELLING
   - The image alone should tell part of the story
   - Use composition, lighting, body language to convey emotion
   - Dramatic elements (mirrors, shadows, light) should serve the story
   - Every element should have narrative purpose

2.5. EMOTIONAL DEPTH - CRITICAL RULE FOR FEAR/ANXIETY SCENES:
   When showing fear, worry, or uncertainty:
   - CREATE AN EMOTIONAL GAP between external world and internal experience
   - At least ONE of these must be present:
     • Facial expression shows deeper emotion than the situation suggests
     • Reflection/shadow/visual element shows internal feeling at different intensity
     • Lighting/composition creates unease, not just a daily scene

   NEVER settle for "oops something happened" - that's an EVENT, not EMOTION

   Quality check (all must be YES):
   ✓ Does the child look troubled even if nothing dangerous happened?
   ✓ Can you understand what the character feels WITHOUT reading text?
   ✓ Does even an adult viewer feel slight discomfort?

   If any answer is NO → the illustration FAILS the emotional depth requirement

3. FOR THIS SPECIFIC PAGE:
   Based on its position in the story arc, focus on:
   {self._extract_focus_areas(story_direction)}

4. STYLE REQUIREMENTS:
   - ILLUSTRATION STYLE - painted/drawn artwork, NOT a photograph
   - Contemporary children's book illustration (think watercolor, digital painting, artistic rendering)
   - Natural Israeli/Mediterranean aesthetic
   - NOT overly cute or Disney-like
   - NOT photorealistic or photo-like
   - Realistic proportions with artistic stylization
   - Painted textures, visible brushstrokes or digital art feel
   - Natural, warm lighting appropriate to mood
   - Muted, earthy color palette

5. CHARACTER CONSISTENCY:
   - Mediterranean/Middle Eastern features
   - Olive/tan skin tone
   - Dark curly hair, brown eyes
   - Realistic, relatable, not generic

6. MAKE IT MEMORABLE:
   - This page should stick in the viewer's mind
   - Create a visual hook that makes you want to turn the page
   - Balance beauty with narrative tension

Create a detailed English prompt that will generate a commercially viable, emotionally resonant ILLUSTRATION (NOT A PHOTOGRAPH).

CRITICAL: The prompt must emphasize this is ILLUSTRATED/PAINTED/DRAWN artwork - NOT a photo or photorealistic image.
Start the prompt with clear art style indicators like "Children's book illustration", "Digital painting", "Watercolor style", etc.

Response format (JSON):
{{
    "english_prompt": "Detailed ILLUSTRATION prompt starting with art style, strong narrative focus...",
    "negative_prompt": "photograph, photo, photorealistic, real photo, camera, lens blur, depth of field, bokeh, visible text, letters, words, writing, alphabet, characters, numbers, digits, Hebrew characters, Arabic script, Latin letters, text on mirrors, text on walls, text on doors, text on pictures, text on frames, text on posters, text on any surface, decorative text, written language, any text whatsoever, gibberish, nonsense characters, random letters, scribbles, handwriting, calligraphy, symbols on walls, writing on surfaces, religious symbols, Star of David, Hamsa, crosses, camels, stereotypical Israeli/Middle Eastern symbols, kitsch cultural iconography, cultural clichés, AND avoid things that harm story impact...",
    "emotional_focus": "The key emotion this image must convey",
    "narrative_hook": "What makes this image memorable",
    "style_tags": ["tag1", "tag2"],
    "recommended_aspect_ratio": "4:3"
}}"""

        response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=1500,
            temperature=0.8,
            system="You are an expert at creating commercially successful children's book illustrations that tell stories visually and connect emotionally with readers.",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        # Parse JSON
        import json
        json_start = content.find('{')
        json_end = content.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            result = json.loads(content[json_start:json_end])

            # Add metadata
            result["story_analysis"] = self.analyzer.analyze_page_position(
                page_number, page_text, None
            )
            result["page_number"] = page_number

            return result
        else:
            raise ValueError("Could not parse JSON from response")

    def _extract_focus_areas(self, story_direction: str) -> str:
        """
        מחלץ את תחומי המיקוד המרכזיים מהניתוח
        """
        lines = story_direction.split('\n')

        # מצא את החלק של VISUAL STORYTELLING PRIORITIES
        focus_lines = []
        in_priorities = False

        for line in lines:
            if 'VISUAL STORYTELLING PRIORITIES:' in line:
                in_priorities = True
                continue
            elif in_priorities and line.strip().startswith('-'):
                focus_lines.append(line.strip())
            elif in_priorities and not line.strip().startswith('-'):
                break

        return '\n   '.join(focus_lines) if focus_lines else "Create strong visual narrative"


# Test
if __name__ == "__main__":
    enhancer = AdvancedPromptEnhancer()

    test_page1 = {
        "page_number": 1,
        "text": 'נועה עמדה מול המראה בחדר האמבטיה, שיערה החום המתולתל קפץ לכל הכיוונים. היא הביטה בעיניים החומות הגדולות שלה וליטפה את פיג\'מת הכוכבים החדשה. "הלילה," אמרה בקול רציני, "אני כבר ילדה גדולה. בלי חיתולים!" הלב שלה דפק חזק. האם היא באמת מוכנה?',
        "visual_description": "נועה עומדת על שרפרף מול מראה גדולה בחדר אמבטיה צבעוני. שיערה החום המתולתל מקופל בצורה מצחיקה. היא לובשת פיג'מה ורודה עם כוכבים זהובים. המראה משקפת את פניה הנחושות אך מודאגות במקצת.",
        "character": "Noa, 5-year-old Israeli girl with Mediterranean features"
    }

    print("Testing Advanced Prompt Enhancer...")
    print("="*60)

    result = enhancer.enhance_with_story_context(
        page_number=test_page1["page_number"],
        page_text=test_page1["text"],
        visual_description=test_page1["visual_description"],
        character_description=test_page1["character"]
    )

    print("\n✅ Enhanced Prompt:")
    print(result["english_prompt"][:300] + "...")
    print(f"\n🎭 Emotional Focus: {result['emotional_focus']}")
    print(f"🎣 Narrative Hook: {result['narrative_hook']}")
    print(f"📍 Story Stage: {result['story_analysis']['arc_stage']}")
