"""
Orchestrator מותאם לעלויות - גרסה חסכונית
משתמש ב-Progressive Quality Strategy
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from cost_optimizer import CostOptimizer, CostEfficientClaudeAgent, CostEfficientOpenAIAgent
from gemini_agent import GeminiAgent
from rating_system import RatingSystem


class OptimizedOrchestrator:
    """
    Orchestrator חסכוני - משתמש במודלים זולים לדראפטים
    """

    def __init__(self, output_dir: str = None):
        # יצירת cost optimizer
        self.cost_optimizer = CostOptimizer()

        # Agents חסכוניים
        self.claude = CostEfficientClaudeAgent(self.cost_optimizer)
        self.openai = CostEfficientOpenAIAgent(self.cost_optimizer)
        self.gemini = GeminiAgent()  # Gemini Flash חינם!

        self.rating_system = RatingSystem()

        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "data"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.topics_dir = self.output_dir / "topics"
        self.stories_dir = self.output_dir / "stories"
        self.ratings_dir = self.output_dir / "ratings"
        self.images_dir = self.output_dir / "images"

        for dir_path in [self.topics_dir, self.stories_dir,
                        self.ratings_dir, self.images_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def create_story_optimized(self, topic: Dict, character: Dict,
                              style_guide: Dict, max_iterations: int = 5) -> Dict:
        """
        יצירת סיפור עם Progressive Quality
        מתחיל זול, משדרג רק אם צריך
        """
        print(f"\n{'='*60}")
        print(f"📖 יצירת סיפור (מותאם עלויות): {topic['name']}")
        print(f"{'='*60}\n")

        iteration = 0
        current_score = 0
        approved_story = None

        while iteration < max_iterations and not approved_story:
            iteration += 1
            print(f"\n--- איטרציה {iteration} ---")

            # בחירת מודלים לפי Progressive Quality
            if iteration == 1:
                strategy = "draft"
            elif current_score < 85:
                strategy = "refinement"
            else:
                strategy = "final"

            claude_model, openai_model = self.cost_optimizer.progressive_quality_strategy(
                strategy, current_score
            )

            print(f"🎯 אסטרטגיה: {strategy}")
            print(f"   Claude: {claude_model}")
            print(f"   OpenAI: {openai_model}")

            # יצירת סיפור
            print(f"\n📝 Claude יוצר סיפור...")
            story_prompt = self._build_story_prompt(topic, character, style_guide)
            story_response = self.claude.generate_with_model(
                prompt=story_prompt,
                system="אתה סופר מוכשר של ספרי ילדים בעברית.",
                model=claude_model,
                temperature=0.9
            )

            # Parse story
            try:
                story = self._parse_json_from_text(story_response["content"])
            except:
                print("⚠️ שגיאה בפרסום JSON, ממשיך...")
                continue

            # הערכה עצמית זולה (pre-filter)
            print(f"\n🔍 Claude מעריך את עצמו (pre-filter)...")
            self_score = self.claude.self_evaluate(
                content=json.dumps(story, ensure_ascii=False),
                criteria="דרג את איכות הסיפור מ-0 ל-100"
            )
            print(f"   Self-score: {self_score}/100")

            # אם הציון העצמי נמוך מדי, לא שולחים ל-OpenAI
            if self_score < 70:
                print(f"   ⏭️ ציון נמוך מדי, מדלג על OpenAI (חוסך כסף!)")
                current_score = self_score
                continue

            # הערכה ב-OpenAI
            print(f"\n🔍 OpenAI מעריך...")
            rating_criteria = self.rating_system.get_rating_prompt("story_rating")
            eval_response = self.openai.evaluate_with_model(
                content=json.dumps(story, ensure_ascii=False)[:3000],  # limit
                criteria=rating_criteria,
                model=openai_model
            )

            try:
                rating_data = json.loads(eval_response["content"])
                current_score = rating_data["weighted_score"]
                print(f"📊 ציון OpenAI: {current_score}/100")
            except:
                print("⚠️ שגיאה בפרסום דירוג")
                continue

            # בדיקת אישור
            if current_score >= 90:
                print(f"✅ סיפור אושר! (ציון {current_score})")
                approved_story = story
            else:
                print(f"❌ טעון שיפור (ציון {current_score} < 90)")

        if not approved_story:
            print(f"⚠️ לא הושג אישור אחרי {max_iterations} איטרציות")
            return None

        # שיפור ויזואלי (Gemini - חינם!)
        print("\n🎨 Gemini משפר תיאורים ויזואליים (חינם!)...")
        enhanced_story = self.gemini.enhance_visual_descriptions(
            approved_story,
            style_guide
        )

        # הכן פרומפטים
        print("🖼️ מכין פרומפטים ל-Nanobana...")
        image_prompts = self.gemini.prepare_for_nanobana(enhanced_story)

        # שמור
        final_output = {
            "topic": topic,
            "character": character,
            "story": enhanced_story,
            "image_prompts": image_prompts,
            "iterations": iteration,
            "final_score": current_score,
            "total_cost": self.cost_optimizer.get_total_cost(),
            "timestamp": datetime.now().isoformat()
        }

        story_id = f"{topic['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_file = self.stories_dir / f"story_{story_id}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ סיפור נשמר ב-{output_file}")

        return final_output

    def _build_story_prompt(self, topic: Dict, character: Dict,
                           style_guide: Dict) -> str:
        """בונה פרומפט ליצירת סיפור"""
        return f"""צור סיפור של 12-15 עמודים.

נושא: {topic['name']}
ערך חינוכי: {topic['educational_value']}

דמות ראשית: {character['name']}
תיאור: {character.get('description', character.get('physical_description', ''))}

סגנון: {style_guide.get('tone', 'חם ומזמין')}

השב בפורמט JSON:
{{
    "title": "שם הספר",
    "pages": [
        {{
            "page_number": 1,
            "text": "טקסט העמוד (50-70 מילים)",
            "visual_description": "תיאור הציור"
        }}
    ],
    "summary": "תקציר",
    "educational_notes": "הערות להורים"
}}
"""

    def _parse_json_from_text(self, text: str) -> Dict:
        """מוצא ומפרסר JSON מתוך טקסט"""
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        raise ValueError("Could not parse JSON")

    def print_final_cost_report(self):
        """מדפיס דוח עלויות סופי"""
        self.cost_optimizer.print_cost_report()


# Demo
if __name__ == "__main__":
    print("🚀 Orchestrator מותאם עלויות - Demo")
    print("="*60)

    orchestrator = OptimizedOrchestrator()

    # טסט עם סיפור אחד
    test_topic = {
        "id": 1,
        "name": "הלילה הראשון בלי חיתול",
        "sub_topics": ["פחד", "גאווה", "תמיכה"],
        "educational_value": "עצמאות והתפתחות"
    }

    test_character = {
        "name": "נועה",
        "description": "ילדה בת 5, אמיצה וסקרנית"
    }

    style_guide = {
        "tone": "חם ומעודד",
        "words_per_page": "50-70",
        "visual_style": "קריקטורי צבעוני"
    }

    story = orchestrator.create_story_optimized(
        topic=test_topic,
        character=test_character,
        style_guide=style_guide,
        max_iterations=3
    )

    print("\n" + "="*60)
    if story:
        print("✅ סיפור נוצר בהצלחה!")
    else:
        print("❌ לא הצלחנו ליצור סיפור")

    # דוח עלויות
    orchestrator.print_final_cost_report()
