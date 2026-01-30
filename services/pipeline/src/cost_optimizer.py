"""
Cost Optimizer - מערכת לאופטימיזציה של עלויות
משתמש במודלים זולים לדראפטים, יקרים רק לפוליש סופי
"""
import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai
from model_config import GEMINI_TEXT_MODEL

load_dotenv()


class CostOptimizer:
    """
    מנהל את המודלים בצורה חסכונית
    """

    # מחירון (למיליון טוקנים)
    PRICING = {
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-haiku-3-5": {"input": 0.25, "output": 1.25},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gemini-flash": {"input": 0.0, "output": 0.0}  # חינם!
    }

    def __init__(self):
        self.total_cost = 0.0
        self.requests_log = []

    def get_cheap_claude(self) -> str:
        """מחזיר Claude זול (Haiku)"""
        return "claude-3-5-haiku-20241022"

    def get_expensive_claude(self) -> str:
        """מחזיר Claude יקר (Sonnet) - רק לפוליש סופי"""
        return "claude-sonnet-4-5-20250929"

    def get_cheap_openai(self) -> str:
        """מחזיר OpenAI זול (mini)"""
        return "gpt-4o-mini"

    def get_expensive_openai(self) -> str:
        """מחזיר OpenAI יקר (4o) - רק לאישור סופי"""
        return "gpt-4o"

    def get_gemini(self) -> str:
        """מחזיר Gemini (Flash - חינם!)"""
        return GEMINI_TEXT_MODEL

    def estimate_tokens(self, text: str) -> int:
        """
        אומדן גס של מספר טוקנים
        בערך 1 טוקן = 4 תווים באנגלית, 2-3 תווים בעברית
        """
        # עברית = בערך 2.5 תווים לטוקן
        return int(len(text) / 2.5)

    def log_request(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        רושם בקשה ומחשב עלות
        """
        pricing = self._get_pricing_for_model(model)

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        self.total_cost += total_cost

        self.requests_log.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost
        })

        return total_cost

    def _get_pricing_for_model(self, model: str) -> Dict:
        """מחזיר מחירון למודל"""
        if "haiku" in model:
            return self.PRICING["claude-haiku-3-5"]
        elif "sonnet" in model or "claude" in model:
            return self.PRICING["claude-sonnet-4-5"]
        elif "mini" in model:
            return self.PRICING["gpt-4o-mini"]
        elif "gpt-4o" in model:
            return self.PRICING["gpt-4o"]
        elif "gemini" in model:
            return self.PRICING["gemini-flash"]
        else:
            return {"input": 0, "output": 0}

    def get_total_cost(self) -> float:
        """מחזיר עלות כוללת"""
        return self.total_cost

    def print_cost_report(self):
        """מדפיס דוח עלויות"""
        print("\n" + "="*60)
        print("💰 דוח עלויות")
        print("="*60)

        model_costs = {}
        for req in self.requests_log:
            model = req["model"]
            if model not in model_costs:
                model_costs[model] = 0
            model_costs[model] += req["cost"]

        for model, cost in sorted(model_costs.items(), key=lambda x: x[1], reverse=True):
            print(f"  {model}: ${cost:.4f}")

        print(f"\n  📊 סה\"כ: ${self.total_cost:.2f}")
        print("="*60)

    def progressive_quality_strategy(self, content_type: str,
                                    current_score: float = 0) -> Tuple[str, str]:
        """
        אסטרטגיית Progressive Quality:
        מתחיל זול, משדרג רק אם צריך

        Returns:
            (claude_model, openai_model)
        """
        if content_type == "draft":
            # דראפט ראשוני - הכי זול
            return self.get_cheap_claude(), self.get_cheap_openai()

        elif content_type == "refinement":
            if current_score < 80:
                # עדיין רחוק, נשאר זול
                return self.get_cheap_claude(), self.get_cheap_openai()
            elif current_score < 88:
                # קרוב, משדרגים את המעריך
                return self.get_cheap_claude(), self.get_expensive_openai()
            else:
                # כמעט שם, משדרגים הכל
                return self.get_expensive_claude(), self.get_expensive_openai()

        elif content_type == "final":
            # פוליש סופי - רק הטוב ביותר
            return self.get_expensive_claude(), self.get_expensive_openai()

        else:
            # ברירת מחדל - זול
            return self.get_cheap_claude(), self.get_cheap_openai()


class CostEfficientClaudeAgent:
    """
    Claude Agent חסכוני
    משתמש בפונקציות של CostOptimizer
    """
    def __init__(self, cost_optimizer: CostOptimizer):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.optimizer = cost_optimizer

    def generate_with_model(self, prompt: str, system: str,
                           model: str = None, temperature: float = 1.0) -> Dict:
        """
        יוצר תוכן עם מודל ספציפי ורושם עלות
        """
        if model is None:
            model = self.optimizer.get_cheap_claude()

        response = self.client.messages.create(
            model=model,
            max_tokens=8000,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )

        # רישום עלות
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = self.optimizer.log_request(model, input_tokens, output_tokens)

        print(f"  💰 {model}: ${cost:.4f} ({input_tokens}→{output_tokens} tokens)")

        return {
            "content": response.content[0].text,
            "cost": cost,
            "model": model
        }

    def self_evaluate(self, content: str, criteria: str) -> float:
        """
        הערכה עצמית זולה של Claude לפני שליחה ל-OpenAI
        """
        prompt = f"""דרג את התוכן הבא לפי הקריטריונים.
תן רק ציון מספרי בין 0-100.

קריטריונים:
{criteria}

תוכן:
{content}

השב רק במספר, ללא הסבר."""

        response = self.generate_with_model(
            prompt=prompt,
            system="אתה מעריך תוכן לפי קריטריונים.",
            model=self.optimizer.get_cheap_claude(),
            temperature=0.3
        )

        try:
            score = float(response["content"].strip())
            return score
        except:
            return 0


class CostEfficientOpenAIAgent:
    """
    OpenAI Agent חסכוני
    """
    def __init__(self, cost_optimizer: CostOptimizer):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.optimizer = cost_optimizer

    def evaluate_with_model(self, content: str, criteria: str,
                           model: str = None) -> Dict:
        """
        מעריך תוכן עם מודל ספציפי
        """
        if model is None:
            model = self.optimizer.get_cheap_openai()

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "אתה מעריך תוכן לספרי ילדים."},
                {"role": "user", "content": f"{criteria}\n\n{content}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # רישום עלות
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = self.optimizer.log_request(model, input_tokens, output_tokens)

        print(f"  💰 {model}: ${cost:.4f} ({input_tokens}→{output_tokens} tokens)")

        return {
            "content": response.choices[0].message.content,
            "cost": cost,
            "model": model
        }


# דוגמה לשימוש
if __name__ == "__main__":
    optimizer = CostOptimizer()

    print("🧪 בדיקת מערכת אופטימיזציה")
    print("="*60)

    # סימולציה של יצירת 100 סיפורים
    print("\n📊 סימולציה: 100 סיפורים")
    print("-"*60)

    # הנחות:
    # - 70% יעברו בפעם הראשונה (draft)
    # - 20% יצטרכו refinement
    # - 10% יצטרכו final polish

    draft_stories = 100
    refinement_stories = 30
    final_stories = 10

    # דראפטים (Haiku + mini)
    for _ in range(draft_stories):
        optimizer.log_request("claude-haiku", 6000, 2000)  # יצירה
        optimizer.log_request("gpt-4o-mini", 8000, 500)    # הערכה

    # שיפורים (Haiku + GPT-4o)
    for _ in range(refinement_stories):
        optimizer.log_request("claude-haiku", 6000, 2000)
        optimizer.log_request("gpt-4o", 8000, 500)

    # פוליש סופי (Sonnet + GPT-4o)
    for _ in range(final_stories):
        optimizer.log_request("claude-sonnet", 6000, 2000)
        optimizer.log_request("gpt-4o", 8000, 500)

    # ויזואלים (Gemini - חינם!)
    for _ in range(100):
        optimizer.log_request("gemini-flash", 8000, 1000)

    optimizer.print_cost_report()

    print("\n💡 השוואה:")
    print(f"  ❌ גישה ישנה (Sonnet + GPT-4o לכולם): ~$110")
    print(f"  ✅ גישה חדשה (Progressive Quality): ~${optimizer.total_cost:.2f}")
    print(f"  💰 חיסכון: ~${110 - optimizer.total_cost:.2f} ({((110 - optimizer.total_cost) / 110 * 100):.0f}%)")
