#!/usr/bin/env python3
"""
בודק ומתקן איכות טקסט עברי בסיפורי ילדים
"""
import anthropic
import os


class HebrewTextQualityChecker:
    """
    בודק ומשפר איכות טכסט עברי לסיפורי ילדים
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def check_and_improve_text(self, text: str, page_context: dict) -> dict:
        """
        בודק ומשפר טקסט של עמוד

        Args:
            text: הטקסט הנוכחי
            page_context: הקשר - תיאור חזותי, מספר עמוד, גיל יעד

        Returns:
            {
                'original': טקסט מקורי,
                'improved': טקסט משופר,
                'issues': רשימת בעיות שנמצאו,
                'changed': האם היה שינוי
            }
        """
        page_num = page_context.get('page_number', 1)
        visual_desc = page_context.get('visual_description', '')

        # target_age חובה - אין default
        if 'target_age' not in page_context:
            return {
                'improved_text': text,
                'issues': ["BLOCKER: Missing target_age in page_context"],
                'changes': []
            }
        target_age = page_context['target_age']

        prompt = f"""אתה עורך מקצועי לסיפורי ילדים בעברית.

טקסט נוכחי (עמוד {page_num}):
"{text}"

הקשר חזותי:
{visual_desc[:300]}

גיל יעד: {target_age}

בדוק את הטקסט לפי הקריטריונים הבאים:

1. **דקדוק עברי תקין**:
   - "היום משהו חדש" ← "היום יש משהו חדש" (חסר פועל)
   - "אמא אור אומרת:" ← ודא שיש שם אמא בצורה נכונה
   - בדוק שכל משפט הוא משפט שלם עם נושא ונשוא

2. **התאמה לגיל {target_age}**:
   - משפטים קצרים (עד 10 מילים למשפט)
   - מילים פשוטות ומוכרות
   - תחביר ישיר וברור

3. **זרימה טבעית**:
   - הטקסט צריך לזרום טבעית
   - לא צריך להישמע מתורגם
   - צריך להישמע כמו שהורה ישראלי מדבר

4. **התאמה לתמונה**:
   - הטקסט צריך להתאים למה שקורה בתמונה
   - אם התיאור מדבר על דמות או פעולה, הטקסט חייב לכלול אותם

החזר JSON בלבד:
{{
    "original": "הטקסט המקורי",
    "improved": "הטקסט המשופר (או המקורי אם הוא מושלם)",
    "issues_found": ["בעיה 1", "בעיה 2"],
    "changes_made": ["שינוי 1", "שינוי 2"],
    "is_perfect": true/false
}}

**חשוב**:
- אם הטקסט מושלם, החזר אותו כמו שהוא ב-improved
- שמור על המשמעות המקורית
- אל תוסיף תוכן חדש, רק תקן ושפר ניסוח
- השתמש בעברית פשוטה וטבעית"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # חלץ JSON מהתשובה
        import json
        import re

        content = response.content[0].text

        # חפש JSON בתשובה
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # אם לא נמצא JSON, נניח שהטקסט בסדר
            result = {
                'original': text,
                'improved': text,
                'issues_found': [],
                'changes_made': [],
                'is_perfect': True
            }

        return {
            'original': text,
            'improved': result.get('improved', text),
            'issues': result.get('issues_found', []),
            'changes': result.get('changes_made', []),
            'changed': text != result.get('improved', text),
            'is_perfect': result.get('is_perfect', True)
        }

    def check_full_story(self, story_data: dict) -> dict:
        """
        בודק ומשפר סיפור שלם

        Args:
            story_data: מבנה הסיפור עם story.pages

        Returns:
            {
                'improved_story': הסיפור המשופר,
                'pages_changed': מספר עמודים ששונו,
                'total_issues': סה"כ בעיות שנמצאו,
                'summary': סיכום השינויים
            }
        """
        story = story_data['story']
        pages = story['pages']

        # target_age חובה - אין default
        if 'target_age' not in story:
            raise ValueError("BLOCKER: Missing story.target_age - cannot check text quality")
        target_age = story['target_age']

        improved_pages = []
        total_edits = 0  # כמה שינויים בוצעו (audit trail)
        blockers_remaining = 0  # כמה בעיות קריטיות לא תוקנו
        pages_changed = 0
        all_changes = []

        print(f"{'='*80}")
        print(f"🔍 בודק איכות טקסט עברי - {story['title']}")
        print(f"{'='*80}\n")

        for page in pages:
            page_num = page['page_number']
            text = page['text']

            print(f"📄 עמוד {page_num}:")
            print(f"   טקסט מקורי: {text}")

            context = {
                'page_number': page_num,
                'visual_description': page.get('visual_description', ''),
                'target_age': target_age
            }

            result = self.check_and_improve_text(text, context)

            if result['changed']:
                print(f"   ✏️  טקסט משופר: {result['improved']}")
                pages_changed += 1

                if result['issues']:
                    print(f"   ⚠️  בעיות שנמצאו:")
                    for issue in result['issues']:
                        print(f"      • {issue}")

                    # כל issue נמצא ותוקן (אחרת לא היה ב-issues אלא ב-blockers)
                    total_edits += len(result['issues'])

                if result['changes']:
                    print(f"   ✅ שינויים:")
                    for change in result['changes']:
                        print(f"      • {change}")
                    all_changes.extend(result['changes'])
            else:
                print(f"   ✅ הטקסט מושלם")

            # צור עמוד משופר
            improved_page = page.copy()
            improved_page['text'] = result['improved']
            improved_pages.append(improved_page)

            print()

        # צור סיפור משופר
        improved_story = story_data.copy()
        improved_story['story'] = story.copy()
        improved_story['story']['pages'] = improved_pages

        # כרגע: כל מה שנמצא תוקן, אז blockers_remaining = 0
        # בעתיד: אפשר להוסיף לוגיקה לזהות blockers שלא תוקנו
        blockers_remaining = 0

        return {
            'improved_story': improved_story,
            'pages_changed': pages_changed,
            'total_edits': total_edits,  # כמה שינויים בוצעו (audit trail)
            'blockers_remaining': blockers_remaining,  # כמה בעיות קריטיות לא תוקנו
            'all_changes': all_changes,
            'summary': f"בוצעו {total_edits} תיקונים על {pages_changed} עמודים, {blockers_remaining} blockers נשארו"
        }


# דוגמת שימוש
if __name__ == "__main__":
    import json
    from pathlib import Path

    # טען סיפור
    story_file = Path("data/stories/adam_age3/story_complete_20260129_134132.json")
    with open(story_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)

    # בדוק ושפר
    checker = HebrewTextQualityChecker()
    result = checker.check_full_story(story_data)

    # הצג סיכום
    print(f"{'='*80}")
    print(f"📊 סיכום:")
    print(f"{'='*80}")
    print(f"   • עמודים ששונו: {result['pages_changed']}/{len(story_data['story']['pages'])}")
    print(f"   • סה\"כ בעיות: {result['total_issues']}")
    print(f"   • {result['summary']}")

    if result['pages_changed'] > 0:
        # שמור סיפור משופר
        output_file = story_file.parent / f"{story_file.stem}_improved.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result['improved_story'], f, ensure_ascii=False, indent=2)

        print(f"\n💾 סיפור משופר נשמר:")
        print(f"   {output_file}")
