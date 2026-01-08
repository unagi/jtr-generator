from __future__ import annotations

from reportlab.pdfbase import pdfmetrics

# 共通実装を再エクスポート（tools/からの参照互換性維持）
from ..helper.fonts import register_font

__all__ = ["register_font", "get_font_metrics"]


def get_font_metrics(font_name: str, font_size: float) -> dict[str, float]:
    ascent = float(pdfmetrics.getAscent(font_name, font_size))
    descent = float(pdfmetrics.getDescent(font_name, font_size))
    height = ascent - descent
    return {
        "ascent": ascent,
        "descent": descent,
        "height": height,
    }
