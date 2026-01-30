"""
Image Generator - מערכת גנרית ליצירת תמונות
תומכת במספר ספקים: DALL-E, Stability AI, וכו'
"""
import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()


class ImageGenerator:
    """
    מחלקה גנרית ליצירת תמונות מפרומפטים
    """

    def __init__(self, provider: str = "dalle"):
        """
        provider: "dalle", "stability", "nanobana"
        """
        self.provider = provider.lower()

        if self.provider == "dalle":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "stability":
            self.api_key = os.getenv("STABILITY_API_KEY")
        elif self.provider == "nanobana":
            # Nano Banana uses Google API key
            self.api_key = os.getenv("GOOGLE_API_KEY")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate_image_dalle(self, prompt: str, style: str = "vivid",
                            size: str = "1024x1024") -> Dict:
        """
        יצירת תמונה עם DALL-E 3

        Args:
            prompt: הפרומפט באנגלית
            style: "vivid" או "natural"
            size: "1024x1024", "1024x1792", "1792x1024"
        """
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            style=style,
            n=1
        )

        return {
            "url": response.data[0].url,
            "revised_prompt": response.data[0].revised_prompt,
            "provider": "dalle"
        }

    def generate_image_stability(self, prompt: str,
                                negative_prompt: str = "",
                                aspect_ratio: str = "1:1") -> Dict:
        """
        יצירת תמונה עם Stability AI (Stable Diffusion)

        Args:
            prompt: הפרומפט באנגלית
            negative_prompt: מה לא לכלול
            aspect_ratio: "1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"
        """
        url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"

        headers = {
            "authorization": f"Bearer {self.api_key}",
            "accept": "image/*"
        }

        files = {"none": ''}
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png"
        }

        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            return {
                "image_data": response.content,
                "provider": "stability"
            }
        else:
            raise Exception(f"Stability API error: {response.status_code} - {response.text}")

    def generate_image_nanobana(self, prompt: str,
                               negative_prompt: str = "",
                               aspect_ratio: str = "4:3",
                               image_size: str = "1K",
                               use_pro: bool = False) -> Dict:
        """
        יצירת תמונה עם Nano Banana (Gemini Image Generation)

        Args:
            prompt: הפרומפט באנגלית
            negative_prompt: מה לא לכלול (לא נתמך ישירות, נשלב בפרומפט)
            aspect_ratio: "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
            image_size: "1K", "2K", "4K" (Pro בלבד)
            use_pro: True = Nano Banana Pro (איכות גבוהה), False = Nano Banana (מהיר)
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("Please install: pip install google-genai")

        # בחירת מודל (צריך models/ prefix)
        model = "models/gemini-3-pro-image-preview" if use_pro else "models/gemini-2.5-flash-image"

        # שילוב negative prompt בפרומפט (Gemini לא תומך בנפרד)
        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}\n\nIMPORTANT: Avoid: {negative_prompt}"

        # אתחול client
        client = genai.Client(api_key=self.api_key)

        # יצירת התמונה
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                )
            )
        )

        # שמירת התמונה
        import tempfile
        import base64
        from io import BytesIO

        for part in response.parts:
            if part.inline_data is not None:
                # קבלת ה-bytes ישירות
                image_data = part.inline_data.data

                return {
                    "image_data": image_data,
                    "provider": "nanobana",
                    "model": model,
                    "aspect_ratio": aspect_ratio,
                    "size": image_size
                }

        raise ValueError("No image generated in response")

    def generate_image(self, prompt: str, **kwargs) -> Dict:
        """
        יצירת תמונה - בוחר את הספק המתאים
        """
        if self.provider == "dalle":
            return self.generate_image_dalle(prompt, **kwargs)
        elif self.provider == "stability":
            return self.generate_image_stability(prompt, **kwargs)
        elif self.provider == "nanobana":
            return self.generate_image_nanobana(prompt, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def save_image(self, image_data: bytes, file_path: str):
        """
        שומר תמונה לדיסק
        """
        with open(file_path, 'wb') as f:
            f.write(image_data)

    def download_image(self, url: str, file_path: str):
        """
        מוריד תמונה מ-URL ושומר
        """
        response = requests.get(url)
        if response.status_code == 200:
            self.save_image(response.content, file_path)
        else:
            raise Exception(f"Failed to download image: {response.status_code}")


class PromptEnhancer:
    """
    משפר תיאורים ויזואליים בעברית לפרומפטים מפורטים באנגלית
    """

    def __init__(self):
        from claude_agent import ClaudeAgent
        self.claude = ClaudeAgent()

    def enhance_visual_description(self, hebrew_description: str,
                                   page_text: str,
                                   character_description: str,
                                   style_guide: Dict) -> Dict:
        """
        ממיר תיאור ויזואלי בעברית לפרומפט מפורט באנגלית
        """
        prompt = f"""Convert this Hebrew visual description to a detailed English prompt for AI image generation (children's book illustration).

Character: {character_description}
Page text: {page_text}
Visual description: {hebrew_description}

Style guide:
- Art style: {style_guide.get('visual_style', 'colorful cartoon')}
- Mood: {style_guide.get('mood', 'warm and encouraging')}
- Target age: 5-8 years old

Create a detailed English prompt that includes:
1. Main scene description
2. Character details (appearance, expression, pose)
3. Background and environment
4. Colors and lighting
5. Art style specifications
6. Mood and atmosphere

Response format (JSON):
{{
    "english_prompt": "Detailed prompt in English...",
    "negative_prompt": "What to avoid (scary, dark, violent, etc.)",
    "style_tags": ["tag1", "tag2", "tag3"],
    "recommended_aspect_ratio": "4:3 or 16:9"
}}"""

        response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert at creating detailed prompts for AI art generation, specializing in children's book illustrations.",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        json_start = content.find('{')
        json_end = content.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            return json.loads(content[json_start:json_end])
        else:
            raise ValueError("Could not parse JSON from response")


# Demo / Test
if __name__ == "__main__":
    print("🎨 Image Generator - Demo")
    print("="*60)

    # Test with DALL-E (שהוא זמין)
    print("\n1. Testing prompt enhancement...")
    enhancer = PromptEnhancer()

    test_description = "נועה עומדת על שרפרף מול מראה גדולה בחדר אמבטיה צבעוני"
    test_text = "נועה עמדה מול המראה בחדר האמבטיה"
    test_character = "ילדה בת 5 עם שיער חום מתולתל"
    test_style = {"visual_style": "קריקטורי צבעוני", "mood": "חם ומעודד"}

    enhanced = enhancer.enhance_visual_description(
        test_description,
        test_text,
        test_character,
        test_style
    )

    print("\n✅ Enhanced prompt:")
    print(json.dumps(enhanced, indent=2, ensure_ascii=False))

    print("\n2. Testing DALL-E image generation...")
    print("   (This will cost ~$0.04)")

    # Uncomment to actually generate:
    # generator = ImageGenerator(provider="dalle")
    # result = generator.generate_image(enhanced["english_prompt"])
    # print(f"\n✅ Image URL: {result['url']}")
    # print(f"   Revised prompt: {result['revised_prompt'][:100]}...")
