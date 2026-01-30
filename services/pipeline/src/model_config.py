"""
Model Configuration - Single Source of Truth for Gemini models and timeouts.
"""
import os

# Text generation (gemini_agent.py)
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash-exp")

# Image generation (image_generator.py, production_image_generator.py)
GEMINI_IMAGE_MODEL_PRO = os.getenv("GEMINI_IMAGE_MODEL_PRO", "models/gemini-3-pro-image-preview")
GEMINI_IMAGE_MODEL_FLASH = os.getenv("GEMINI_IMAGE_MODEL_FLASH", "models/gemini-2.5-flash-image")

# Timeout for all Gemini API calls (seconds)
GEMINI_TIMEOUT_SEC = int(os.getenv("GEMINI_TIMEOUT_SEC", "30"))
