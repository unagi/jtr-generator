"""
履歴書PDF生成モジュール

このモジュールは、事前に抽出された罫線データ（JSON）を使用して
JIS規格準拠の履歴書PDFを生成します。
"""

import json
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_resume_pdf(
    data: dict[str, Any],
    options: dict[str, Any],
    output_path: Path,
) -> None:
    """
    履歴書PDFを生成する

    Args:
        data: 履歴書データ（現在は未使用、テキスト描画時に使用）
        options: 生成オプション（paper_size, date_format等）
        output_path: 出力先PDFファイルパス
    """
    # 罫線データのJSONファイルパス（レイアウト定義データ）
    # TODO: options経由で指定できるようにする（A4/B5切り替え対応）
    lines_json_path = Path(__file__).parent.parent.parent / "data/layouts/resume_layout_a4.json"

    with open(lines_json_path, encoding="utf-8") as f:
        lines_data = json.load(f)

    # A4サイズのCanvasを作成
    c = canvas.Canvas(str(output_path), pagesize=A4)

    # Page 1: 罫線を描画
    _draw_lines(c, lines_data["page1_lines"])
    c.showPage()

    # Page 2: 罫線を描画
    _draw_lines(c, lines_data["page2_lines"])
    c.showPage()

    c.save()


def _draw_lines(c: canvas.Canvas, lines: list[list[float]]) -> None:
    """
    罫線を描画する

    Args:
        c: ReportLabのCanvasオブジェクト
        lines: 線分データのリスト [[x0, y0, x1, y1, width], ...]
    """
    for line in lines:
        x0, y0, x1, y1, width = line
        c.setLineWidth(width)
        c.line(x0, y0, x1, y1)
