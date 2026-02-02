"""
Orchestrator - מנהל את התהליך המלא של יצירת הספרים
מתאם בין Claude, OpenAI ו-Gemini עד להשגת ציון 90+
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from claude_agent import ClaudeAgent
from openai_agent import OpenAIAgent
from gemini_agent import GeminiAgent
from rating_system import RatingSystem


class Orchestrator:
    def __init__(self, output_dir: str = None):
        self.claude = ClaudeAgent()
        self.openai = OpenAIAgent()
        self.gemini = GeminiAgent()
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

    def generate_topics_with_approval(self, num_topics: int = 100,
                                     max_iterations: int = 5) -> List[Dict]:
        """
        שלב 1: יצירת נושאים עם אישור
        Claude מציע -> OpenAI מעריך -> איטרציות עד ציון 90+
        """
        print(f"\n{'='*60}")
        print(f"🎯 שלב 1: יצירת {num_topics} נושאים")
        print(f"{'='*60}\n")

        approved_topics = []
        iteration = 0
        feedback = None

        while len(approved_topics) < num_topics and iteration < max_iterations:
            iteration += 1
            print(f"\n--- איטרציה {iteration} ---")

            # Claude מציע נושאים
            print("📝 Claude מציע נושאים...")
            topics_needed = num_topics - len(approved_topics)
            proposed = self.claude.generate_topics(
                num_topics=topics_needed,
                existing_feedback=feedback
            )

            # OpenAI מעריך
            print("🔍 OpenAI מעריך את ההצעות...")
            evaluations = self.openai.rate_topics(proposed['topics'])

            # סינון נושאים מאושרים
            new_approved = [
                eval_result for eval_result in evaluations
                if eval_result['approved']
            ]

            approved_topics.extend(new_approved)

            # סטטיסטיקה
            approved_count = len(new_approved)
            total_proposed = len(proposed['topics'])
            print(f"✅ אושרו: {approved_count}/{total_proposed}")
            print(f"📊 סה״כ מאושרים עד כה: {len(approved_topics)}/{num_topics}")

            # אם יש נושאים שלא אושרו, הכן משוב
            if approved_count < total_proposed:
                rejected = [
                    eval_result for eval_result in evaluations
                    if not eval_result['approved']
                ]

                feedback = self._compile_feedback(rejected)
                print(f"\n💡 משוב ל-Claude:")
                print(feedback[:200] + "...")

            # שמור נתונים ביניים
            self._save_topics_iteration(iteration, evaluations, approved_topics)

        # שמור תוצאות סופיות
        final_topics = [item['topic'] for item in approved_topics[:num_topics]]
        output_file = self.topics_dir / f"approved_topics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_topics": len(final_topics),
                "iterations": iteration,
                "timestamp": datetime.now().isoformat(),
                "topics": final_topics
            }, f, ensure_ascii=False, indent=2)

        print(f"\n✅ הושלם! {len(final_topics)} נושאים נשמרו ב-{output_file}")
        return final_topics

    def generate_characters_with_approval(self, num_characters: int = 10,
                                         max_iterations: int = 5) -> List[Dict]:
        """
        שלב 2: יצירת דמויות עם אישור
        """
        print(f"\n{'='*60}")
        print(f"👥 שלב 2: יצירת {num_characters} דמויות")
        print(f"{'='*60}\n")

        approved_characters = []
        iteration = 0
        feedback = None

        while len(approved_characters) < num_characters and iteration < max_iterations:
            iteration += 1
            print(f"\n--- איטרציה {iteration} ---")

            print("📝 Claude מציע דמויות...")
            chars_needed = num_characters - len(approved_characters)
            proposed = self.claude.propose_characters(
                num_characters=chars_needed,
                existing_feedback=feedback
            )

            print("🔍 OpenAI מעריך...")
            evaluations = self.openai.rate_characters(proposed['characters'])

            new_approved = [
                eval_result for eval_result in evaluations
                if eval_result['approved']
            ]

            approved_characters.extend(new_approved)

            approved_count = len(new_approved)
            total_proposed = len(proposed['characters'])
            print(f"✅ אושרו: {approved_count}/{total_proposed}")
            print(f"📊 סה״כ: {len(approved_characters)}/{num_characters}")

            if approved_count < total_proposed:
                rejected = [e for e in evaluations if not e['approved']]
                feedback = self._compile_feedback(rejected)

        final_characters = [item['character'] for item in approved_characters[:num_characters]]
        output_file = self.output_dir / f"approved_characters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_characters": len(final_characters),
                "iterations": iteration,
                "timestamp": datetime.now().isoformat(),
                "characters": final_characters
            }, f, ensure_ascii=False, indent=2)

        print(f"\n✅ הושלם! {len(final_characters)} דמויות נשמרו ב-{output_file}")
        return final_characters

    def create_story_with_approval(self, topic: Dict, character: Dict,
                                   style_guide: Dict, max_iterations: int = 5) -> Dict:
        """
        שלב 3: יצירת סיפור בודד עם אישור
        """
        print(f"\n{'='*60}")
        print(f"📖 יצירת סיפור: {topic['name']}")
        print(f"{'='*60}\n")

        iteration = 0
        feedback = None
        approved_story = None

        while iteration < max_iterations and not approved_story:
            iteration += 1
            print(f"\n--- איטרציה {iteration} ---")

            print("📝 Claude כותב סיפור...")
            story = self.claude.create_story(
                topic=topic,
                character=character,
                style_guide=style_guide,
                existing_feedback=feedback
            )

            print("🔍 OpenAI מעריך...")
            evaluation = self.openai.rate_story(story, topic)

            score = evaluation['rating']['weighted_score']
            print(f"📊 ציון: {score}/100")

            if evaluation['approved']:
                print("✅ סיפור אושר!")
                approved_story = story
            else:
                print(f"❌ סיפור לא אושר (ציון {score} < 90)")
                feedback = evaluation['rating']['suggestions']
                print(f"💡 משוב: {feedback[:200]}...")

            # שמור איטרציה
            self._save_story_iteration(iteration, topic, story, evaluation)

        if not approved_story:
            print(f"⚠️ לא הושג אישור אחרי {max_iterations} איטרציות")
            return None

        # שלב 4: שיפור תיאורים ויזואליים עם Gemini
        print("\n🎨 Gemini משפר תיאורים ויזואליים...")
        enhanced_story = self.gemini.enhance_visual_descriptions(
            approved_story,
            style_guide
        )

        # הכן פרומפטים ל-Nanobana
        print("🖼️ מכין פרומפטים ל-Nanobana...")
        image_prompts = self.gemini.prepare_for_nanobana(enhanced_story)

        # שמור תוצאה סופית
        final_output = {
            "topic": topic,
            "character": character,
            "story": enhanced_story,
            "image_prompts": image_prompts,
            "iterations": iteration,
            "final_score": score,
            "timestamp": datetime.now().isoformat()
        }

        story_id = f"{topic['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_file = self.stories_dir / f"story_{story_id}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ סיפור מלא נשמר ב-{output_file}")

        # שמור פרומפטים נפרדים לנוחות
        prompts_file = self.images_dir / f"prompts_{story_id}.json"
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(image_prompts, f, ensure_ascii=False, indent=2)

        print(f"🖼️ פרומפטים לתמונות נשמרו ב-{prompts_file}")

        return final_output

    def _compile_feedback(self, rejected_items: List[Dict]) -> str:
        """
        מרכז משוב מפריטים שנדחו
        """
        feedback_parts = []
        for item in rejected_items:
            rating = item['rating']
            feedback_parts.append(f"- {rating['reasoning']}")
            if 'suggestions' in rating:
                feedback_parts.append(f"  הצעות: {rating['suggestions']}")

        return "\n".join(feedback_parts)

    def _save_topics_iteration(self, iteration: int, evaluations: List[Dict],
                               approved_so_far: List[Dict]):
        """
        שומר נתוני איטרציה של נושאים
        """
        iteration_file = self.ratings_dir / f"topics_iteration_{iteration}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(iteration_file, 'w', encoding='utf-8') as f:
            json.dump({
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "evaluations": evaluations,
                "total_approved": len(approved_so_far)
            }, f, ensure_ascii=False, indent=2)

    def _save_story_iteration(self, iteration: int, topic: Dict,
                             story: Dict, evaluation: Dict):
        """
        שומר נתוני איטרציה של סיפור
        """
        iteration_file = self.ratings_dir / f"story_{topic['id']}_iteration_{iteration}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(iteration_file, 'w', encoding='utf-8') as f:
            json.dump({
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "topic": topic,
                "story": story,
                "evaluation": evaluation
            }, f, ensure_ascii=False, indent=2)


# Main execution flow
if __name__ == "__main__":
    print("🚀 מערכת יצירת ספרי ילדים - Claude x OpenAI x Gemini")
    print("="*60)

    orchestrator = Orchestrator()

    # שלב 1: נושאים
    topics = orchestrator.generate_topics_with_approval(num_topics=5)  # Test with 5

    # שלב 2: דמויות
    characters = orchestrator.generate_characters_with_approval(num_characters=3)  # Test with 3

    # שלב 3: סיפור ראשון
    if topics and characters:
        style_guide = {
            "tone": "חם, מעודד ומלא הומור עדין",
            "words_per_page": "50-70",
            "visual_style": "איורים קריקטוריים צבעוניים בסגנון מודרני",
            "mood": "אופטימי ומעצים"
        }

        first_story = orchestrator.create_story_with_approval(
            topic=topics[0],
            character=characters[0],
            style_guide=style_guide
        )

        print("\n🎉 תהליך הושלם בהצלחה!")
