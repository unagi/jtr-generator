from __future__ import annotations

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_font(font_path: Path) -> str:
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")

    font_name = font_path.stem
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    return font_name


def get_font_metrics(font_name: str, font_size: float) -> dict[str, float]:
    ascent = float(pdfmetrics.getAscent(font_name, font_size))
    descent = float(pdfmetrics.getDescent(font_name, font_size))
    height = ascent - descent
    return {
        "ascent": ascent,
        "descent": descent,
        "height": height,
    }
