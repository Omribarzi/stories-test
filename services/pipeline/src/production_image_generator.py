#!/usr/bin/env python3
"""
Production Image Generator - יצירת תמונות ברמת ייצור
כולל negative prompts, quality gates, ו-validation
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class ProductionImageGenerator:
    """
    מחלקה ליצירת תמונות ברמת production
    מטפלת ב-gibberish text, consistency, quality gates
    """

    # Negative prompts to prevent gibberish and kitsch symbols
    FORBIDDEN_ELEMENTS = [
        "no visible text in the scene",
        "no letters or words on objects",
        "no Hebrew characters visible",
        "no Arabic script",
        "no written text on walls or objects",
        "no religious symbols (Star of David, Hamsa, crosses)",
        "no camels",
        "no stereotypical Israeli/Middle Eastern symbols",
        "no kitsch cultural iconography",
        "no cultural clichés",
        "clean illustration without text overlays"
    ]

    # Visual quality requirements
    QUALITY_REQUIREMENTS = {
        "composition": "child-friendly, clear focal point",
        "colors": "warm, vibrant, age-appropriate",
        "detail_level": "rich but not overwhelming",
        "emotional_tone": "encouraging and safe"
    }

    def __init__(self, provider: str = "nanobana"):
        """
        provider: "dalle" or "nanobana"
        """
        self.provider = provider.lower()

        if self.provider == "dalle":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "nanobana":
            self.api_key = os.getenv("GOOGLE_API_KEY")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def build_negative_prompt(self, additional_negatives: List[str] = None) -> str:
        """
        בונה negative prompt מלא
        """
        all_negatives = self.FORBIDDEN_ELEMENTS.copy()
        if additional_negatives:
            all_negatives.extend(additional_negatives)

        return ", ".join(all_negatives)

    def generate_interior_page(self,
                              page_text: str,
                              visual_description: str,
                              character_description: str,
                              style_guide: Dict,
                              page_number: int) -> Dict:
        """
        יוצר תמונה לעמוד פנימי בספר

        Returns:
            {
                "image_data": bytes,
                "prompt_used": str,
                "page_type": "interior"
            }
        """
        # Build enhanced prompt
        negative_prompt = self.build_negative_prompt()

        base_prompt = f"""Children's book illustration for ages 5-8, Israeli/Mediterranean setting.

Scene: {visual_description}
Character: {character_description}
Page text context: {page_text}

Style requirements:
- Art style: {style_guide.get('visual_style', 'colorful, warm cartoon illustration')}
- Mood: {style_guide.get('mood', 'encouraging and safe')}
- Composition: Clear focal point, child-friendly
- Colors: Warm, vibrant, Mediterranean palette
- Detail: Rich but not overwhelming

CRITICAL REQUIREMENTS:
- {negative_prompt}
- Character consistency is essential
- Israeli/Mediterranean aesthetic (warm lighting, local setting)
- Age-appropriate emotions and expressions
- Safe, encouraging atmosphere

Page {page_number} of 15-page story."""

        if self.provider == "dalle":
            return self._generate_dalle(base_prompt, "interior")
        elif self.provider == "nanobana":
            return self._generate_nanobana(base_prompt, negative_prompt, "interior")

    def generate_cover_page(self,
                           story_title: str,
                           story_summary: str,
                           character_description: str,
                           style_guide: Dict) -> Dict:
        """
        יוצר כריכה מקצועית לספר

        DIFFERENT from interior pages:
        - Full-bleed composition
        - More complex, panoramic scene
        - Title integration considerations
        - Higher visual density
        """
        negative_prompt = self.build_negative_prompt([
            "no white margins",
            "no empty space around edges"
        ])

        cover_prompt = f"""Professional children's book COVER illustration, full-bleed edge-to-edge artwork.

Story: {story_title}
Summary: {story_summary}
Main character: {character_description}

COVER-SPECIFIC REQUIREMENTS:
- FULL-BLEED composition (edge-to-edge, no margins)
- Rich, detailed panoramic scene with multiple elements
- Dynamic composition with depth and layers
- Multiple characters or activities showing story essence
- Atmospheric background (not flat)
- Professional book cover quality
- Space for title overlay at top (keep top third less busy)

Style:
- {style_guide.get('visual_style', 'colorful, warm cartoon')}
- Israeli/Mediterranean aesthetic
- Warm, inviting lighting
- Ages 5-8 appropriate

CRITICAL:
- {negative_prompt}
- This is a COVER, not an interior page - make it bold and engaging
- Edge-to-edge artwork, full bleed
- Rich visual storytelling"""

        if self.provider == "dalle":
            return self._generate_dalle(cover_prompt, "cover")
        elif self.provider == "nanobana":
            return self._generate_nanobana(cover_prompt, negative_prompt, "cover")

    def _generate_dalle(self, prompt: str, page_type: str) -> Dict:
        """Generate with DALL-E 3"""
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",  # Landscape for children's book
            quality="standard",
            style="vivid",
            n=1
        )

        # Download image
        import requests
        image_url = response.data[0].url
        image_data = requests.get(image_url).content

        return {
            "image_data": image_data,
            "prompt_used": prompt,
            "revised_prompt": response.data[0].revised_prompt,
            "page_type": page_type,
            "provider": "dalle"
        }

    def _generate_nanobana(self, prompt: str, negative_prompt: str,
                          page_type: str) -> Dict:
        """Generate with Nano Banana (Gemini)"""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("pip install google-genai")

        # Integrate negative prompt
        full_prompt = f"{prompt}\n\nAVOID: {negative_prompt}"

        # Use Pro for covers, Flash for interior
        from model_config import GEMINI_IMAGE_MODEL_PRO, GEMINI_IMAGE_MODEL_FLASH
        model = GEMINI_IMAGE_MODEL_PRO if page_type == "cover" else GEMINI_IMAGE_MODEL_FLASH

        client = genai.Client(api_key=self.api_key)

        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",  # Landscape children's book
                )
            )
        )

        # Extract image
        for part in response.parts:
            if part.inline_data is not None:
                return {
                    "image_data": part.inline_data.data,
                    "prompt_used": prompt,
                    "page_type": page_type,
                    "provider": "nanobana",
                    "model": model
                }

        raise ValueError("No image generated")

    def validate_image(self, image_data: bytes) -> Dict:
        """
        בדיקת איכות תמונה (placeholder - ניתן להרחיב)

        Returns:
            {
                "valid": bool,
                "issues": List[str],
                "warnings": List[str]
            }
        """
        # TODO: Add actual validation
        # - OCR detection for pseudo-text
        # - Symbol detection
        # - Color analysis
        # - Composition checks

        return {
            "valid": True,
            "issues": [],
            "warnings": []
        }


# Demo
if __name__ == "__main__":
    print("🎨 Production Image Generator - Demo")
    print("="*60)

    gen = ProductionImageGenerator(provider="nanobana")

    print("\n✅ Negative prompts:")
    print(gen.build_negative_prompt())

    print("\n✅ Ready to generate production-quality images")
    print("   - Interior pages: clean, no gibberish")
    print("   - Cover pages: full-bleed, professional")
