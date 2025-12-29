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
    # 罫線データのJSONファイルパス（v2フォーマット）
    # TODO: options経由で指定できるようにする（A4/B5切り替え対応）
    lines_json_path = Path(__file__).parent.parent.parent / "data/layouts/resume_layout_a4_v2.json"

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


def _draw_lines(c: canvas.Canvas, lines: list[dict[str, Any]]) -> None:
    """
    罫線を完全な描画設定で描画する（v2フォーマット対応）

    Args:
        c: ReportLabのCanvasオブジェクト
        lines: 線分データのリスト（dict形式、v2フォーマット）
    """
    for line in lines:
        # 線幅設定
        c.setLineWidth(line["width"])

        # 線種設定（破線パターン）
        dash_pattern = line.get("dash_pattern", [])
        dash_phase = line.get("dash_phase", 0)
        if dash_pattern and len(dash_pattern) > 0:
            # ReportLabは偶数要素を期待（奇数の場合は2回繰り返して周期維持）
            if len(dash_pattern) % 2 != 0:
                dash_pattern = dash_pattern * 2
            c.setDash(dash_pattern, dash_phase)
        else:
            c.setDash()  # 実線にリセット

        # 端部形状設定（0=butt, 1=round, 2=square）
        cap = line.get("cap", 2)
        c.setLineCap(cap)

        # 接合形状設定（0=mitre, 1=round, 2=bevel）
        join = line.get("join", 1)
        c.setLineJoin(join)

        # 色設定（RGB: 0.0-1.0）
        color = line.get("color", [0.0, 0.0, 0.0])
        c.setStrokeColorRGB(*color)

        # 線を描画
        c.line(line["x0"], line["y0"], line["x1"], line["y1"])
