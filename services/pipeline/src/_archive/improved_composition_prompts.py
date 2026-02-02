#!/usr/bin/env python3
"""
Improved Composition Prompts - פרומפטים משופרים לקומפוזיציה טובה יותר
"""


def get_improved_layout_prompt(character_description: str) -> str:
    """
    מחזיר prompt משופר לקומפוזיציה עם מקום טקסט
    """
    return f"""CRITICAL COMPOSITION REQUIREMENT - READ THIS FIRST:

IMAGE LAYOUT (MOST IMPORTANT):
This is a WIDE HORIZONTAL SHOT (16:9 landscape) designed for Hebrew text placement.
Think of the image divided into LEFT 60% and RIGHT 40% sections.

LEFT 60% (Main Scene):
- ALL characters, objects, and action happen HERE
- The child character ({character_description})
- Any furniture, mirrors, doors, or scene elements
- This is the "active" storytelling zone

RIGHT 40% (EMPTY NEGATIVE SPACE):
- PLAIN EMPTY WALL - completely clear
- UNIFORM COLOR - single wall tone, no patterns
- NO objects extending into this area
- NO decorations, posters, shadows, or visual elements
- This MUST stay completely empty for Hebrew text overlay
- Imagine a TEXT ZONE sign here - nothing can enter

COMPOSITION RULES:
✓ Wide shot showing full scene from left to right
✓ Camera angle captures entire horizontal space
✓ Main subject positioned at LEFT THIRD of frame (rule of thirds)
✓ Supporting elements in CENTER THIRD
✓ RIGHT THIRD is empty negative space (plain wall)
✓ Think: "storytelling on left, empty space on right"

VISUAL EXAMPLE:
Imagine a theater stage - actors perform on the left 2/3,
the right 1/3 is just plain backdrop with nothing on it.

CHARACTER ACCURACY:
The main character must precisely match: {character_description}
Pay special attention to:
- Exact age appearance (toddler proportions if 2 years old)
- Hair texture (smooth/straight vs curly)
- Facial features matching the description

ABSOLUTELY NO TEXT ANYWHERE:
- NO text, letters, symbols, or gibberish on ANY surface
- Mirrors: completely plain and reflective
- Walls: plain painted surfaces, NO posters with text
- NO decorative elements with text or letter-like shapes
- NO Hebrew, Arabic, English, or any language
- If you think it might look like text - don't include it

STYLE:
- Children's book illustration (painted/illustrated, NOT a photograph)
- Warm, natural lighting
- Contemporary but timeless aesthetic
- Emotionally resonant and commercially viable"""


def get_ultra_strong_negative_prompt() -> str:
    """
    מחזיר negative prompt חזק מאוד
    """
    return """text, writing, letters, words, symbols, numbers, alphabet, characters,
typography, font, calligraphy, handwriting, inscriptions, labels, signs,
Hebrew text, Hebrew letters, Hebrew characters, Hebrew script,
Arabic text, Arabic letters, Arabic script, Arabic characters,
English text, Latin alphabet, Roman letters, English words,
text on mirrors, writing on mirrors, letters reflected in mirrors, mirror inscriptions,
text on walls, writing on walls, wall posters with text, framed text on walls,
text on doors, door signs, door labels, door numbers,
text on any surface, writing on any surface, text overlay,
decorative text, ornamental letters, artistic text elements,
gibberish, nonsense text, random letters, scrambled characters, letter-like shapes,
unclear writing, illegible text, abstract letter forms,
posters with writing, pictures with captions, framed art with text,
religious text, religious symbols with text,
Star of David, Hamsa, crosses, crescents, religious iconography,
camels, stereotypical Middle Eastern symbols, cultural clichés,
compositions where subject fills entire frame,
centered composition, subject in middle of frame,
cluttered right side, objects on right side, furniture on right side,
decorations on right wall, posters on right wall, shadows on right wall,
photograph, photo, photorealistic, real photo, camera shot,
lens blur, bokeh, depth of field blur, camera lens effects"""


def build_full_prompt(base_prompt: str, character_description: str) -> str:
    """
    בונה prompt מלא עם כל השיפורים
    """
    # שים את הקומפוזיציה בהתחלה!
    layout_prompt = get_improved_layout_prompt(character_description)

    # הרכב: קומפוזיציה -> תיאור הסצנה -> דגשים נוספים
    full_prompt = f"""{layout_prompt}

SCENE DESCRIPTION:
{base_prompt}

FINAL EMPHASIS - CRITICAL REQUIREMENTS:
1. COMPOSITION: LEFT 60% has all content, RIGHT 40% is EMPTY WALL
2. CHARACTER: Must exactly match the description provided
3. NO TEXT: Zero text or text-like elements anywhere in image
4. STYLE: Illustrated children's book art (not a photograph)

Remember: The right side of the image MUST be completely empty and clear!"""

    return full_prompt


# Test
if __name__ == "__main__":
    print("📋 Improved Composition Prompts")
    print("=" * 80)

    test_description = "2-year-old boy with smooth straight light brown hair"
    test_scene = "Boy standing at bathroom sink, looking in mirror"

    full = build_full_prompt(test_scene, test_description)

    print("\n🎨 Full Prompt Preview:")
    print(full[:500] + "...\n")

    print("✅ Ready to use!")
