#!/usr/bin/env python3
"""
Image Validator - בודק תמונות עם Claude Vision API
"""
import base64
from pathlib import Path
from typing import Dict, Tuple
from claude_agent import ClaudeAgent


class ImageValidator:
    """
    מערכת בדיקה אוטומטית לתמונות - משתמש ב-Claude Vision API
    """

    def __init__(self):
        self.claude = ClaudeAgent()
        self.client = self.claude.client
        self.model = self.claude.model

    def validate_image(self, image_path: Path,
                      page_context: Dict = None) -> Tuple[bool, str, Dict]:
        """
        בודק תמונה לפי קריטריונים ברורים

        Args:
            image_path: נתיב לתמונה
            page_context: הקשר של העמוד (מספר, תיאור דמות, וכו')

        Returns:
            (passed, reason, details) - האם עבר, סיבה, פרטים נוספים
        """
        # קרא ואנקוד תמונה
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # בנה קריטריונים בהתאם להקשר
        criteria = self._build_criteria(page_context)

        # שלח לClaude Vision
        prompt = f"""You are a quality control system for children's book illustrations.
Analyze this image and check if it meets ALL the following criteria:

{criteria}

CRITICAL VALIDATION RULES (Priority Order):

1. TEXT/GIBBERISH CHECK (CRITICAL - MUST PASS):
   - Scan the ENTIRE image for any text, letters, symbols, or gibberish
   - Check mirrors, walls, doors, posters, ANY surface
   - Even small or unclear letter-like shapes count as FAIL
   - Hebrew/Arabic/English/any language = FAIL
   - This is the MOST IMPORTANT criterion - be very strict here

2. CHARACTER CHECK (CRITICAL - MUST PASS):
   - Verify character matches description precisely
   - Check hair type (smooth/straight vs curly), hair color, age appearance
   - Check clothing (star-pattern pajamas if specified)
   - Child should look the correct age (toddler if 2 years old)
   - Be strict on these details

3. PARENT GENDER CHECK (IMPORTANT if applicable):
   - If mother appears, must look female
   - If father appears, must look male
   - Check clothing, hair, facial features

4. TEXT SPACE CHECK (CRITICAL FOR iPAD VERSION):
   - RIGHT 1/3 (approximately 33%) of image MUST be empty plain wall
   - This area should be ONE UNIFORM COLOR matching the room
   - NO objects, furniture, or character parts should extend into this area
   - Small shadows or gentle gradients are OK
   - The wall should be continuous from top to bottom
   - Think: "Can I place 4-5 lines of Hebrew text here without overlapping the illustration?"
   - STRICT: If illustration extends past 70% mark, it's TOO MUCH - FAIL
   - PASS: If right 30%+ is clearly empty and uniform

Response format (JSON):
{{
    "passed": true/false,
    "criteria_results": {{
        "no_text_or_gibberish": {{
            "passed": true/false,
            "details": "detailed explanation of what you see"
        }},
        "text_space_adequate": {{
            "passed": true/false,
            "details": "description of right 1/3 area - is it empty and uniform? Does illustration stay in left 2/3?"
        }},
        "character_accurate": {{
            "passed": true/false,
            "details": "how well character matches description"
        }},
        "parent_gender_correct": {{
            "passed": true/false,
            "details": "parent gender verification if applicable"
        }}
    }},
    "overall_verdict": "PASS or FAIL",
    "reason": "clear explanation of why it passed or failed",
    "suggestions": "what to fix if failed"
}}

STRICTNESS LEVELS:
- TEXT/GIBBERISH: Be VERY STRICT - any text = FAIL
- CHARACTER: Be STRICT - must match description
- TEXT SPACE: Be MODERATELY STRICT - need clear 30%+ empty wall on right
- PARENT GENDER: Be MODERATE - should match but minor variations OK

Overall verdict should be PASS if:
- NO text/gibberish (MUST pass)
- Character matches reasonably well (MUST pass)
- Right 30%+ is empty uniform wall (SHOULD pass - be reasonable)
- Parent gender correct if applicable
"""

        # קרא לClaude Vision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        # פרסר תשובה
        content = response.content[0].text

        # חלץ JSON - מצא את האובייקט הראשון המאוזן
        import json
        json_start = content.find('{')

        if json_start == -1:
            return False, "Failed to find JSON in response", {}

        # מצא את ה-} התואם
        brace_count = 0
        json_end = json_start

        for i in range(json_start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break

        if json_end > json_start:
            try:
                result = json.loads(content[json_start:json_end])

                passed = result.get('overall_verdict', 'FAIL') == 'PASS'
                reason = result.get('reason', 'Unknown reason')
                details = result.get('criteria_results', {})

                return passed, reason, details
            except json.JSONDecodeError as e:
                return False, f"JSON parsing error: {str(e)}", {}
        else:
            # אם לא הצליח לפרסר - נכשל
            return False, "Failed to parse validation response", {}

    def _build_criteria(self, page_context: Dict = None) -> str:
        """
        בונה קריטריונים בהתאם להקשר
        """
        criteria = []

        # קריטריונים בסיסיים תמיד (בסדר עדיפות)
        criteria.append("✓ CRITICAL: NO TEXT OR GIBBERISH anywhere in the image (mirrors, walls, any surface)")
        criteria.append("✓ IMPORTANT: RIGHT 1/3 (30-35%) is EMPTY PLAIN WALL with uniform color - no objects, no character parts")
        criteria.append("✓ IMPORTANT: Illustration stays in LEFT 2/3 (66%) - doesn't extend past 70% mark")
        criteria.append("✓ Wall color should be uniform and match the room's aesthetic")

        if page_context:
            # תיאור דמות
            if 'character_description' in page_context:
                criteria.append(f"✓ Character matches: {page_context['character_description']}")

            # הורים
            if 'mother_present' in page_context and page_context['mother_present']:
                criteria.append(f"✓ Mother (named {page_context.get('mother_name', 'אור')}) appears as FEMALE")

            if 'father_present' in page_context and page_context['father_present']:
                criteria.append(f"✓ Father (named {page_context.get('father_name', 'עמרי')}) appears as MALE")

        return '\n'.join(criteria)

    def print_validation_report(self, passed: bool, reason: str, details: Dict):
        """
        מדפיס דוח בדיקה ויזואלי
        """
        print("\n" + "=" * 80)
        if passed:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        print("=" * 80)

        print(f"\n📊 Reason: {reason}")

        if details:
            print("\n📋 Detailed Results:")
            for criterion, result in details.items():
                status = "✅" if result.get('passed', False) else "❌"
                print(f"\n{status} {criterion.replace('_', ' ').title()}:")
                print(f"   {result.get('details', 'No details')}")

        print("\n" + "=" * 80)


# Test
if __name__ == "__main__":
    validator = ImageValidator()

    # בדוק תמונה לדוגמה
    test_image = Path("data/images/adam_book/page_01_empty_v2.png")

    if test_image.exists():
        print(f"🔍 בודק תמונה: {test_image}")

        context = {
            'character_description': '2-year-old boy with smooth straight light brown hair',
            'mother_present': False,
            'father_present': False
        }

        passed, reason, details = validator.validate_image(test_image, context)
        validator.print_validation_report(passed, reason, details)
    else:
        print(f"❌ תמונה לא נמצאה: {test_image}")
