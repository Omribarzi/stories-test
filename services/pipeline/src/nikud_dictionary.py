#!/usr/bin/env python3
"""
מילון ניקוד מצטבר - Cumulative Nikud Dictionary
מילון שנבנה אוטומטית ומתעדכן עם כל שימוש
"""
import json
from pathlib import Path
from typing import Dict, Tuple, List
import re


class NikudDictionary:
    """
    מילון ניקוד שמתעדכן אוטומטית
    כל פעם שקוראים ל-API, המילים החדשות נשמרות עם metadata
    """

    def __init__(self, dict_path: Path = None, run_id: str = None):
        if dict_path is None:
            dict_path = Path("data/.nikud_dictionary/words.json")

        self.dict_path = dict_path
        self.dict_path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or "unknown"

        # טען מילון קיים
        self.words = self._load_dictionary()

    def _load_dictionary(self) -> Dict:
        """טוען מילון מהדיסק - תומך במבנה ישן וחדש"""
        if self.dict_path.exists():
            with open(self.dict_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # המר מבנה ישן לחדש אם צריך
            converted = {}
            for key, value in raw_data.items():
                if isinstance(value, str):
                    # מבנה ישן: {word: nikud_text}
                    converted[key] = {
                        "text": value,
                        "source": "cache",  # נניח שזה מ-cache
                        "first_seen_run_id": "legacy",
                        "count_uses": 1
                    }
                elif isinstance(value, dict):
                    # מבנה חדש: {word: {text, source, ...}}
                    converted[key] = value

            return converted
        return {}

    def _save_dictionary(self):
        """שומר מילון לדיסק"""
        with open(self.dict_path, 'w', encoding='utf-8') as f:
            json.dump(self.words, f, ensure_ascii=False, indent=2)

    def _tokenize_hebrew(self, text: str) -> list:
        """מפצל טקסט למילים עבריות"""
        # הסר פיסוק, שמור רק אותיות עבריות (+ ניקוד)
        words = re.findall(r'[\u0590-\u05FF]+', text)
        return words

    def add_from_text(self, plain_text: str, nikud_text: str, source: str = "api"):
        """
        מוסיף מילים חדשות מזוג טקסט רגיל ← → מנוקד

        Args:
            plain_text: טקסט ללא ניקוד
            nikud_text: אותו טקסט עם ניקוד
            source: מקור הניקוד ("api" או "cache")
        """
        plain_words = self._tokenize_hebrew(plain_text)
        nikud_words = self._tokenize_hebrew(nikud_text)

        # ודא שמספר המילים תואם
        if len(plain_words) != len(nikud_words):
            print(f"⚠️  Warning: word count mismatch ({len(plain_words)} vs {len(nikud_words)})")
            return

        # עדכן מילון
        new_words = 0
        updated_words = 0

        for plain, nikud in zip(plain_words, nikud_words):
            if plain not in self.words:
                # מילה חדשה
                self.words[plain] = {
                    "text": nikud,
                    "source": source,
                    "first_seen_run_id": self.run_id,
                    "count_uses": 1
                }
                new_words += 1
            else:
                # מילה קיימת - עדכן count
                self.words[plain]["count_uses"] = self.words[plain].get("count_uses", 0) + 1
                updated_words += 1

        if new_words > 0 or updated_words > 0:
            self._save_dictionary()
            if new_words > 0:
                print(f"   📚 מילון: +{new_words} מילים חדשות (סה\"כ {len(self.words)} מילים)")

    def apply_nikud(self, text: str) -> Tuple[str, List[str], Dict[str, str]]:
        """
        מנקד טקסט באמצעות המילון

        Returns:
            (nikud_text, missing_words, word_sources)
            - nikud_text: טקסט מנוקד
            - missing_words: רשימת מילים שחסרות במילון
            - word_sources: {word: source} - מקור לכל מילה שנוקדה
        """
        words = self._tokenize_hebrew(text)
        missing = []
        word_sources = {}

        for word in words:
            if word not in self.words:
                missing.append(word)
            else:
                word_sources[word] = self.words[word].get("source", "cache")

        # החלף כל מילה במילון
        result = text
        for plain, data in self.words.items():
            nikud = data["text"] if isinstance(data, dict) else data
            # החלפה רק של מילים שלמות (לא חלק ממילה)
            result = re.sub(rf'\b{re.escape(plain)}\b', nikud, result)

        return result, missing, word_sources

    def get_stats(self) -> dict:
        """סטטיסטיקות מילון"""
        sources_count = {}
        for data in self.words.values():
            if isinstance(data, dict):
                source = data.get("source", "unknown")
                sources_count[source] = sources_count.get(source, 0) + 1

        return {
            "total_words": len(self.words),
            "dict_path": str(self.dict_path),
            "sources": sources_count,
            "sample_words": list(self.words.items())[:5]
        }


# דוגמה לשימוש
if __name__ == "__main__":
    dictionary = NikudDictionary(run_id="test_run_123")

    # הוסף מילים למילון
    plain = "רועי יושב על הרצפה"
    nikud = "רוֹעִי יוֹשֵׁב עַל הָרִצְפָּה"
    dictionary.add_from_text(plain, nikud, source="api")

    # נסה לנקד טקסט חדש
    new_text = "רועי הולך על הרצפה"
    result, missing, sources = dictionary.apply_nikud(new_text)

    print(f"מקורי: {new_text}")
    print(f"מנוקד: {result}")
    print(f"חסר במילון: {missing}")
    print(f"מקורות: {sources}")
    print(f"\nסטטיסטיקות: {dictionary.get_stats()}")
