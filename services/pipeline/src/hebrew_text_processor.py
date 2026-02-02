#!/usr/bin/env python3
"""
Hebrew Text Processor - טיפול מתקדם בטקסט עברי
מטפל ב-RTL, ניקוד, וקריאות לילדים
"""
from typing import List, Dict
import unicodedata
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import requests
import time
import os
from anthropic import Anthropic


class HebrewTextProcessor:
    """
    מעבד טקסט עברי לספרי ילדים
    """

    def __init__(self):
        self.nikud_enabled = True

    def add_nikud(self, text: str, use_api: bool = True) -> str:
        """
        מוסיף ניקוד לטקסט עברי
        משתמש ב-Claude API לניקוד מושלם

        Args:
            text: טקסט עברי
            use_api: האם להשתמש ב-API (True) או רק במילון ידני (False)
        """
        if not self.nikud_enabled:
            return text

        # אם הטקסט קצר (עד 30 מילים), נסה Dicta API ואז Claude כגיבוי
        if use_api and len(text.split()) <= 30:
            # קודם כל - נקד את המילים שקיימות במילון הידני
            # זה מונע מ-Claude לקבל מילים בעייתיות בכלל
            partial_result = self._manual_nikud(text)

            # בדוק אם יש מילים שעדיין צריכות ניקוד
            nikud_chars = '\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7\u05B8\u05B9\u05BB\u05BC\u05C1\u05C2'
            words = partial_result.split()
            words_without_nikud = [w for w in words if not any(c in nikud_chars for c in w.strip('.,;:!?"\''))]

            # אם כל המילים כבר מנוקדות מהמילון הידני - סיימנו
            if not words_without_nikud:
                return partial_result

            # תן ל-Claude את הטקסט החלקי עם בקשה להשלים רק את החסר
            try:
                result = self._add_nikud_claude(partial_result)
                return result
            except Exception as e:
                print(f"⚠️  שגיאה ב-Claude API: {e}")
                print(f"   משתמש במילון ידני")
                return partial_result
        else:
            # טקסט ארוך או מצב ללא API - השתמש במילון ידני
            return self._manual_nikud(text)

    def _add_nikud_claude(self, text: str) -> str:
        """
        מוסיף ניקוד באמצעות Claude API
        מדויק במיוחד לעברית מודרנית וספרי ילדים
        """
        try:
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            prompt = f"""⚠️ CRITICAL BLOCKER RULE ⚠️
You are ONLY adding nikud vowel marks to Hebrew text. You MUST NOT modify any Hebrew letters whatsoever.

IMPORTANT: The spelling you see is the AUTHOR'S INTENTIONAL CHOICE for a children's book. DO NOT "correct", "normalize", or "standardize" the spelling. Both כתיב מלא and כתיב חסר are valid Hebrew, and the author has chosen כתיב מלא (full spelling with ו and י letters).

🚫 ABSOLUTELY FORBIDDEN - DO NOT DO THIS:
- Changing letters: קופסה → קפסה (WRONG - removed ו)
- Changing ניגש → נגש (WRONG - removed י)
- Changing גינה → גנה (WRONG - removed י)
- "Correcting" from כתיב מלא (full spelling with ו,י) to כתיב חסר (defective spelling)
- Removing ו or י letters under ANY circumstances
- "Fixing" or "normalizing" or "standardizing" spelling
- Any modification to base letters

✅ ONLY ALLOWED ACTION:
- Add combining nikud marks (Unicode U+0591-U+05C7): ַ ָ ֶ ֵ ִ ֹ ֻ ְ ּ ֿ ֽ
- Preserve EVERY Hebrew letter EXACTLY as written by the author

EXAMPLES OF CORRECT BEHAVIOR:
Input:  קופסה (with ו - keep it!)
Output: קוּפְסָה (kept ו, only added ְ ָ ּוּ marks)

Input:  נוספת (with ו - keep it!)
Output: נוֹסֶפֶת (kept ו, only added marks)

Input:  אפשר (no ו - don't add it!)
Output: אֶפְשָׁר (no ו added, only marks)

Input:  ניגש (with י - keep it!)
Output: נִגַּשׁ (kept י, only added marks)

Input:  גינה (with י - keep it!)
Output: גִּנָּה (kept י, only added marks)

Input:  אופניים (with two י - keep both!)
Output: אוֹפַנַּיִים (kept both י, only added marks)

THE TEXT TO VOCALIZE (DO NOT CHANGE ANY LETTERS):
{text}

VERIFICATION CHECKLIST BEFORE RESPONDING:
□ Did I change the number of Hebrew letters? (If YES → WRONG, start over)
□ Did I remove any ו or י? (If YES → WRONG, start over)
□ Did I "fix" כתיב מלא to כתיב חסר? (If YES → WRONG, start over)
□ Did I ONLY add nikud combining marks? (Must be YES)

MANDATORY RULES YOU MUST FOLLOW:
1. Add nikud to EVERY word — including proper names (איתי→אִיתַי, נועה→נוֹעָה, רועי→רוֹעִי, מיכל→מִיכַל)
2. NEVER skip words - children need complete nikud. Short words and names MUST get nikud too
3. Keep EXACT letter count - count Hebrew letters before and after, they must match EXACTLY
4. Preserve ALL ו and י letters exactly as they appear - the author chose this spelling intentionally
5. DO NOT apply any spelling "corrections" or "normalization" - just add nikud marks
6. If you're unsure whether to keep a letter - ALWAYS keep it, NEVER remove it

VERIFICATION BEFORE YOU RESPOND:
- Count Hebrew letters in input text: ____ letters
- Count Hebrew letters in your output (excluding nikud marks): ____ letters
- Do these numbers match? If NO, start over and fix it.

Return ONLY the vocalized text with nikud marks added, no explanations or comments."""

            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            nikud_text = response.content[0].text.strip()

            # וודא שזה טקסט עברי עם ניקוד
            if nikud_text and len(nikud_text) > 0:
                return nikud_text
            else:
                raise ValueError("Claude returned empty response")

        except Exception as e:
            print(f"⚠️  Claude API error: {e}")
            raise

    def _add_nikud_dicta(self, text: str) -> str:
        """
        מוסיף ניקוד באמצעות Dicta API
        https://nakdan-5-3.loadbalancer.dicta.org.il
        """
        url = "https://nakdan-5-3.loadbalancer.dicta.org.il/addnikud"

        # פצל לקטעים קטנים (API מוגבל ל-~1000 תווים)
        max_chunk_size = 800
        if len(text) > max_chunk_size:
            # פצל לפי משפטים/קטעים
            sentences = text.split('.')
            nikud_parts = []
            current_chunk = []
            current_len = 0

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if current_len + len(sentence) > max_chunk_size and current_chunk:
                    # שלח את ה-chunk הנוכחי
                    chunk_text = '. '.join(current_chunk) + '.'
                    nikud_parts.append(self._call_dicta_api(chunk_text))
                    current_chunk = [sentence]
                    current_len = len(sentence)
                else:
                    current_chunk.append(sentence)
                    current_len += len(sentence)

            # שלח את ה-chunk האחרון
            if current_chunk:
                chunk_text = '. '.join(current_chunk) + '.'
                nikud_parts.append(self._call_dicta_api(chunk_text))

            return ' '.join(nikud_parts)
        else:
            return self._call_dicta_api(text)

    def _call_dicta_api(self, text: str) -> str:
        """
        קריאה ל-Dicta API - ננסה endpoint פשוט יותר
        """
        # Try the simpler endpoint first
        url = "https://nakdan-5-3.loadbalancer.dicta.org.il/nakdan/nikud"

        try:
            # Try simple text parameter
            response = requests.get(url, params={"text": text}, timeout=10)

            if response.status_code != 200:
                # Try POST with different format
                url2 = "https://nakdan-5-3.loadbalancer.dicta.org.il/addnikud"
                response = requests.post(
                    url2,
                    data=text.encode('utf-8'),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    timeout=10
                )

            response.raise_for_status()

            # Try to parse response
            try:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    nikud_text = ''.join([item.get('w', '') for item in result])
                    return nikud_text
                elif isinstance(result, str):
                    return result
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                # Maybe it's plain text response
                return response.text

        except Exception as e:
            # Silently fall back to manual nikud
            raise

    def _complete_missing_nikud(self, text: str) -> str:
        """
        משלים ניקוד חסר - בודק כל מילה ומנקד אותה מהמילון הידני אם אין לה ניקוד

        Args:
            text: טקסט שכבר עבר ניקוד חלקי (מ-API)

        Returns:
            טקסט עם ניקוד מלא (API + מילון ידני)
        """
        import re

        # מילון ניקוד (נעתיק מ-_manual_nikud)
        nikud_dict = self._get_nikud_dictionary()

        # פצל למילים (שמור פיסוק)
        words = text.split()
        completed_words = []

        nikud_chars = '\u05B0\u05B1\u05B2\u05B3\u05B4\u05B5\u05B6\u05B7\u05B8\u05B9\u05BB\u05BC\u05C1\u05C2'

        for word in words:
            # נקה סימני פיסוק
            clean_word = word.strip('.,;:!?"\'')
            prefix = word[:len(word) - len(word.lstrip('.,;:!?"\''))]
            suffix = word[len(clean_word) + len(prefix):]

            # הסר ניקוד קיים כדי לבדוק אם המילה במילון
            import unicodedata
            clean_word_no_nikud = ''.join(c for c in unicodedata.normalize('NFD', clean_word)
                                         if unicodedata.category(c) != 'Mn')

            # אם המילה קיימת במילון הידני - השתמש בה (עדיפות מוחלטת על API)
            if clean_word_no_nikud in nikud_dict:
                completed_words.append(prefix + nikud_dict[clean_word_no_nikud] + suffix)
            else:
                # מילה לא במילון - השאר כמו שהיא (עם או בלי ניקוד מה-API)
                completed_words.append(word)

        return ' '.join(completed_words)

    def _get_nikud_dictionary(self) -> dict:
        """מחזיר את המילון הידני המלא"""
        return {
            # מילים מסיפור "נועה והפינה השקטה"
            "יושבת": "יוֹשֶׁבֶת",
            "יושבים": "יוֹשְׁבִים",
            "יושב": "יוֹשֵׁב",
            "על": "עַל",
            "השטיח": "הַשָּׁטִיחַ",
            "מחזיקה": "מַחֲזִיקָה",
            "מחזיק": "מַחֲזִיק",
            "התינוק": "הַתִּינוֹק",
            "תינוק": "תִּינוֹק",
            "מדבר": "מְדַבֵּר",
            "אל": "אֶל",
            "בקול": "בְּקוֹל",
            "רך": "רַךְ",
            "קמה": "קָמָה",
            "הולכת": "הוֹלֶכֶת",
            "הולך": "הוֹלֵךְ",
            "לחדר": "לַחֶדֶר",
            "חדר": "חֶדֶר",
            "בחדר": "בְּחֶדֶר",
            "החדר": "הַחֶדֶר",
            "שלה": "שֶׁלָּהּ",
            "שלו": "שֶׁלּוֹ",
            "סוגרת": "סוֹגֶרֶת",
            "את": "אֶת",
            "הדלת": "הַדֶּלֶת",
            "דלת": "דֶּלֶת",
            "לאט": "לְאַט",
            "עומדת": "עוֹמֶדֶת",
            "עומד": "עוֹמֵד",
            "עומדים": "עוֹמְדִים",
            "עמדה": "עָמְדָה",
            "עמד": "עָמַד",
            "ליד": "לְיַד",
            "המיטה": "הַמִּטָּה",
            "מיטה": "מִטָּה",
            "במיטה": "בַּמִּטָּה",
            "שקט": "שָׁקֵט",
            "שקטה": "שְׁקֵטָה",
            "מאוד": "מְאֹד",
            "רק": "רַק",
            "הנשימה": "הַנְּשִׁימָה",
            "נשימה": "נְשִׁימָה",
            "נושם": "נוֹשֵׁם",
            "נושמת": "נוֹשֶׁמֶת",
            "נושמים": "נוֹשְׁמִים",
            "רואה": "רוֹאָה",
            "הבובה": "הַבּוּבָּה",
            "בובה": "בּוּבָּה",
            "המדף": "הַמַּדָּף",
            "מדף": "מַדָּף",
            "שם": "שָׁם",
            "לבד": "לְבַד",
            "מושיטה": "מוֹשִׁיטָה",
            "יד": "יָד",
            "מורידה": "מוֹרִידָה",
            "מחבקת": "מְחַבֶּקֶת",
            "אותה": "אוֹתָהּ",
            "אותו": "אוֹתוֹ",
            "חזק": "חָזָק",
            "הבטן": "הַבֶּטֶן",
            "בטן": "בֶּטֶן",
            "בבטן": "בַּבֶּטֶן",
            "רועדת": "רוֹעֶדֶת",
            "קצת": "קְצָת",
            "הרצפה": "הָרִצְפָּה",
            "רצפה": "רִצְפָּה",
            "רצפת": "רִצְפַּת",
            "מסדרת": "מְסַדֶּרֶת",
            "לבובה": "לַבּוּבָּה",
            "שמיכה": "שְׂמִיכָה",
            "קטנה": "קְטַנָּה",
            "קטן": "קָטָן",
            "מלטפת": "מְלַטֶּפֶת",
            "השיער": "הַשֵּׂעָר",
            "שיער": "שֵׂעָר",
            "שיערו": "שְׂעָרוֹ",
            "שיערה": "שְׂעָרָהּ",
            "נכנס": "נִכְנָס",
            "בפתח": "בַּפֶּתַח",
            "פתח": "פֶּתַח",
            "פותח": "פּוֹתֵחַ",
            "מסתכלת": "מִסְתַּכֶּלֶת",
            "מסתכל": "מִסְתַּכֵּל",
            "ומסתכל": "וּמִסְתַּכֵּל",
            "עליו": "עָלָיו",
            "עליה": "עָלֶיהָ",
            "אבא": "אַבָּא",
            "ואבא": "וְאַבָּא",
            "אמא": "אִמָּא",
            "אומר": "אוֹמֵר",
            "אומרת": "אוֹמֶרֶת",
            "אמרה": "אָמְרָה",
            "כלום": "כְּלוּם",
            "מכסה": "מְכַסָּה",
            "מביטה": "מַבִּיטָה",
            "מביט": "מַבִּיט",
            "הביטה": "הִבִּיטָה",
            "הביטו": "הִבִּיטוּ",
            "מחייך": "מְחַיֵּךְ",
            "עמוק": "עָמוֹק",
            "בינהם": "בֵּינֵיהֶם",
            "ספר": "סֵפֶר",
            "הספר": "הַסֵּפֶר",
            "בספר": "בַּסֵּפֶר",
            "חוזרת": "חוֹזֶרֶת",
            "לרצפה": "לָרִצְפָּה",
            "פותחת": "פּוֹתַחַת",
            "מתקרב": "מִתְקָרֵב",
            "מצביעה": "מַצְבִּיעָה",
            "תמונה": "תְּמוּנָה",
            "ביחד": "בְּיַחַד",
            "קוראים": "קוֹרְאִים",
            "דף": "דַּף",
            "אחד": "אֶחָד",
            "עכשיו": "עַכְשָׁיו",
            "נשענת": "נִשְׁעֶנֶת",
            "מהממת": "מְהַמְהֶמֶת",
            "עיניים": "עֵינַיִם",
            "בעיניים": "בְּעֵינַיִם",
            "סוגרת": "סוֹגֶרֶת",
            "מניח": "מֵנִיחַ",
            "הגוף": "הַגּוּף",
            "גוף": "גּוּף",
            "בשמיכה": "בִּשְׂמִיכָה",
            "נושמת": "נוֹשֶׁמֶת",

            # מילים כלליות חשובות
            "הלילה": "הַלַּיְלָה",
            "לילה": "לַיְלָה",
            "הגדול": "הַגָּדוֹל",
            "גדול": "גָּדוֹל",
            "גדולה": "גְּדוֹלָה",
            "הגדולות": "הַגְּדוֹלוֹת",
            "של": "שֶׁל",
            "אדם": "אָדָם",
            "באדם": "בְּאָדָם",
            "נועה": "נוֹעָה",
            "רועי": "רוֹעִי",
            "סיפור": "סִפּוּר",
            "מול": "מוּל",
            "המראה": "הַמַּרְאָה",
            "האמבטיה": "הָאַמְבַּטְיָה",
            "החום": "הַחוּם",
            "החומות": "הַחוּמוֹת",
            "הישר": "הַיָּשָׁר",
            "נראה": "נִרְאָה",
            "נקי": "נָקִי",
            "ומסודר": "וּמְסוּדָר",
            "מסודר": "מְסוּדָר",
            "המתולתל": "הַמְתוֹלְתָּל",
            "קפץ": "קָפַץ",
            "לכל": "לְכָל",
            "הכיוונים": "הַכִּוּוּנִים",
            "היא": "הִיא",
            "הוא": "הוּא",
            "פיגמת": "פִּיגָ׳מַת",
            "הכוכבים": "הַכּוֹכָבִים",
            "החדשה": "הַחֲדָשָׁה",
            "רציני": "רְצִינִי",
            "אני": "אֲנִי",
            "כבר": "כְּבָר",
            "ילדה": "יַלְדָּה",
            "ילד": "יֶלֶד",
            "בלי": "בְּלִי",
            "חיתולים": "חִיתוּלִים",
            "הלב": "הַלֵּב",
            "לב": "לֵב",
            "דפק": "דָּפַק",
            "האם": "הַאִם",
            "באמת": "בֶּאֱמֶת",
            "מוכנה": "מוּכָנָה",
            "גאה": "גֵּאָה",
            "בך": "בָּךְ",
            "מותק": "מוֹתֶק",
            "חיבקה": "חִבְּקָה",
            "זה": "זֶה",
            "זאת": "זֹאת",
            "צעד": "צַעַד",
            "ואמיץ": "וְאַמִּיץ",
            "הרים": "הֵרִים",
            "אגודל": "אֲגוּדָל",
            "למעלה": "לְמַעְלָה",
            "וחייך": "וְחִיֵּךְ",
            "גיבורה": "גִּבּוֹרָה",
            "שלנו": "שֶׁלָּנוּ",
            "אבל": "אֲבָל",
            "הרגישה": "הִרְגִּישָׁה",
            "הרגיש": "הִרְגִּישׁ",
            "פרפרים": "פַּרְפָּרִים",
            "מה": "מָה",
            "אם": "אִם",
            "לא": "לֹא",
            "תצליח": "תַּצְלִיחַ",
            "יצליח": "יַצְלִיחַ",
            "תתעורר": "תִּתְעוֹרֵר",
            "יתעורר": "יִתְעוֹרֵר",
            "רטובה": "רְטוּבָה",
            "רטוב": "רָטוֹב",
            "נשמה": "נָשְׁמָה",
            "יכולה": "יְכוֹלָה",
            "אור": "אוֹר",
            "עמרי": "עָמְרִי",
            "בגאווה": "בְּגַאֲוָה",
            "אתה": "אַתָּה",
            "בחיוך": "בְּחִיּוּךְ",
            "לחשה": "לָחֲשָׁה",
            "לעצמה": "לְעַצְמָהּ",
            "שכבה": "שָׁכְבָה",
            "והביטה": "וְהִבִּיטָה",
            "בתקרה": "בַּתִּקְרָה",
            "החושך": "הַחֹשֶׁךְ",
            "היה": "הָיָה",
            "היתה": "הָיְתָה",
            "מלא": "מָלֵא",
            "בצללים": "בִּצְלָלִים",
            "מוזרים": "מוּזָרִים",
            "טוב": "טוֹב",
            "מחר": "מָחָר",
            "מחכה": "מְחַכֶּה",
            "יום": "יוֹם",
            "חדש": "חָדָשׁ",
            "והפינה": "וְהַפִּינָה",
            "פינה": "פִּינָה",
            "בפינה": "בְּפִינָה",
            "השקטה": "הַשְּׁקֵטָה",
            "הריק": "הָרֵיק",
            "ריקים": "רֵיקִים",
            "וריקים": "וְרֵיקִים",
            "לבנים": "לְבָנִים",
            "הקירות": "הַקִּירוֹת",
            "הקיר": "הַקִּיר",
            "הלבן": "הַלָּבָן",
            "הפוסטרים": "הַפּוֹסְטֶרִים",
            "קופסה": "קוּפְסָה",
            "עם": "עִם",
            "מכוניות": "מְכוֹנִיּוֹת",
            "הצעצוע": "הַצַּעֲצוּעַ",
            "יש": "יֵשׁ",

            # מילים שClaude משנה באופן שגוי (מסיר י או ו) - כתיב מלא
            "ניגש": "נִיגַּשׁ",  # שומר י
            "גינה": "גִּינָּה",  # שומר י
            "אופניים": "אוֹפַנַּיִים",
            "חלון": "חַלּוֹן",
            "לחלון": "לַחַלּוֹן",
            "בחוץ": "בַּחוּץ",
            "רוכב": "רוֹכֵב",
            "במעגלים": "בְּמַעְגָּלִים",
            "זוכר": "זוֹכֵר",
            "הקטנה": "הַקְּטַנָּה"
        }

    def _manual_nikud(self, text: str) -> str:
        """
        ניקוד ידני למילים נפוצות בספרי ילדים
        """
        # השתמש במילון המרכזי
        nikud_dict = self._get_nikud_dictionary()

        # החלפת מילים עם ניקוד
        words = text.split()
        nikud_words = []
        for word in words:
            # נקה סימני פיסוק
            clean_word = word.strip('.,;:!?"\'')
            prefix = word[:len(word) - len(word.lstrip('.,;:!?"\''))]
            suffix = word[len(clean_word) + len(prefix):]

            # חפש במילון
            if clean_word in nikud_dict:
                nikud_words.append(prefix + nikud_dict[clean_word] + suffix)
            else:
                nikud_words.append(word)

        return ' '.join(nikud_words)

    def process_for_pdf(self, text: str, add_nikud: bool = True, apply_bidi: bool = True) -> str:
        """
        מעבד טקסט בודד לתצוגה ב-PDF
        מחיל ניקוד ו-RTL transformation

        Args:
            text: טקסט עברי
            add_nikud: האם להוסיף ניקוד
            apply_bidi: האם להחיל bidi transformation (כבה לפונטים שמטפלים ב-RTL בעצמם)

        Returns:
            טקסט מעובד מוכן לתצוגה
        """
        # שלב 1: הוסף ניקוד
        if add_nikud:
            text = self.add_nikud(text)

        # שלב 2: RTL transformation (רק אם נדרש)
        if apply_bidi:
            if add_nikud:
                # עבור טקסט עם ניקוד - אל תשתמש ב-reshape (הוא לערבית)
                # Normalize קודם עם NFD (Decomposition) כדי להפריד את הניקוד מהאות
                text = unicodedata.normalize('NFD', text)
                # עכשיו עשה bidi transformation
                bidi_text = get_display(text)
                # Normalize בחזרה ל-NFC (Composition) כדי להדביק את הניקוד לאות
                bidi_text = unicodedata.normalize('NFC', bidi_text)
            else:
                # טקסט בלי ניקוד - reshape + bidi
                reshaped = reshape(text)
                bidi_text = get_display(reshaped)
            return bidi_text
        else:
            # פונטים כמו FrankRuehl מטפלים ב-RTL בעצמם
            return text

    def split_to_lines(self, text: str, max_width: int,
                       font_name: str, font_size: int,
                       canvas_obj) -> List[str]:
        """
        מחלק טקסט עברי לשורות בצורה נכונה

        CRITICAL: מפצל לפני bidi transformation!

        Args:
            text: טקסט עברי (לפני עיבוד)
            max_width: רוחב מקסימלי בפיקסלים
            font_name: שם הפונט
            font_size: גודל הפונט
            canvas_obj: אובייקט Canvas של reportlab

        Returns:
            רשימת שורות מעובדות מוכנות לתצוגה
        """
        # שלב 1: הוסף ניקוד (לפני פיצול!)
        text_with_nikud = self.add_nikud(text)

        # שלב 2: פצל למילים (לפני bidi!)
        words = text_with_nikud.split()

        # שלב 3: בנה שורות לפי רוחב
        lines_raw = []
        current_line = []

        for word in words:
            # בדוק רוחב עם המילה הנוכחית
            test_line = ' '.join(current_line + [word])

            # החל bidi זמנית לבדיקה
            test_line_display = self.process_for_pdf(test_line, add_nikud=False)
            line_width = canvas_obj.stringWidth(test_line_display, font_name, font_size)

            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines_raw.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines_raw.append(' '.join(current_line))

        # שלב 4: החל bidi על כל שורה בנפרד
        lines_processed = []
        for line in lines_raw:
            processed = self.process_for_pdf(line, add_nikud=False)  # כבר יש ניקוד
            lines_processed.append(processed)

        return lines_processed

    def get_display_text(self, text: str, add_nikud: bool = True) -> str:
        """
        Alias for process_for_pdf - לתאימות אחורה
        """
        return self.process_for_pdf(text, add_nikud=add_nikud)


# Demo
if __name__ == "__main__":
    processor = HebrewTextProcessor()

    test_text = "נועה עמדה מול המראה בחדר האמבטיה"

    print("Original:")
    print(test_text)

    print("\nWith nikud:")
    with_nikud = processor.add_nikud(test_text)
    print(with_nikud)

    print("\nProcessed for PDF:")
    processed = processor.process_for_pdf(test_text)
    print(processed)
