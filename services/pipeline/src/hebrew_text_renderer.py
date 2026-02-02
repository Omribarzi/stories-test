"""
Hebrew text renderer with proper nikud positioning.

Uses Pillow + libraqm (HarfBuzz + fribidi) for text shaping.
Handles GPOS mark-to-base positioning for nikud marks.
Text is rendered to transparent PNG images, then placed in the PDF.
"""
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features
from reportlab.lib.utils import ImageReader

if not features.check('raqm'):
    print("WARNING: libraqm not available. Nikud positioning may be imprecise.")


class HebrewTextRenderer:
    """Renders Hebrew text with proper nikud to transparent PNG images."""

    def __init__(self, font_path: str):
        """
        Args:
            font_path: Path to the .ttf font file
        """
        self.font_path = Path(font_path)
        self._render_scale = 4  # Render at 4x for sharp nikud marks
        self._font_cache = {}
        self._has_raqm = features.check('raqm')

    def _get_font(self, size):
        """Get cached Pillow ImageFont."""
        if size not in self._font_cache:
            self._font_cache[size] = ImageFont.truetype(
                str(self.font_path), int(size))
        return self._font_cache[size]

    def _draw_kwargs(self):
        """RTL direction kwargs when raqm is available."""
        if self._has_raqm:
            return {'direction': 'rtl'}
        return {}

    def render_line(self, text: str, font_size: float, color=(0, 0, 0)):
        """Render a line of text to transparent PNG.

        Args:
            text: Hebrew text (logical order)
            font_size: Font size in PDF points
            color: RGB tuple (0-1 range)

        Returns:
            (PIL Image, img_w_pdf, img_h_pdf, text_w_pdf, descent_pdf)
        """
        render_size = font_size * self._render_scale
        font = self._get_font(render_size)
        kwargs = self._draw_kwargs()

        # Measure text
        bbox = font.getbbox(text, **kwargs)
        text_width = bbox[2] - bbox[0]
        ascent = -bbox[1]
        descent = bbox[3]

        pad = 4
        img_w = int(text_width + 2 * pad + 10)
        img_h = int(ascent + descent + 2 * pad + 10)

        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        draw.text((pad - bbox[0], pad), text,
                  fill=(r, g, b, 255), font=font, **kwargs)

        # Convert to PDF points
        s = self._render_scale
        return img, img_w / s, img_h / s, text_width / s, descent / s

    def draw_right_aligned(self, canvas_obj, text_x: float, y: float,
                           text: str, font_size: float, color=(0, 0, 0)):
        """Render text and place in PDF, right-aligned at text_x.

        Args:
            canvas_obj: reportlab Canvas
            text_x: Right edge x position
            y: Baseline y position
            text: Hebrew text (logical order)
            font_size: Font size in PDF points
            color: RGB tuple (0-1 range)
        """
        img, img_w_pdf, img_h_pdf, text_w_pdf, descent_pdf = \
            self.render_line(text, font_size, color)

        # Right-align: image right edge at text_x
        x = text_x - img_w_pdf

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        # Vertical positioning
        img_y = y - descent_pdf - 4

        canvas_obj.drawImage(
            ImageReader(buf),
            x, img_y,
            width=img_w_pdf, height=img_h_pdf,
            mask='auto'
        )

        return text_w_pdf

    def measure_width(self, text: str, font_size: float) -> float:
        """Measure text width in PDF points without rendering."""
        render_size = font_size * self._render_scale
        font = self._get_font(render_size)
        bbox = font.getbbox(text, **self._draw_kwargs())
        return (bbox[2] - bbox[0]) / self._render_scale
