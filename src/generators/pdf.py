"""
履歴書PDF生成モジュール

このモジュールは、事前に抽出された罫線データ（JSON）を使用して
JIS規格準拠の履歴書PDFを生成します。
"""

import json
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def _find_default_font() -> Path:
    """
    デフォルトフォント（BIZ UDMincho）のパスを取得

    Returns:
        デフォルトフォントの絶対パス

    Raises:
        FileNotFoundError: フォントファイルが存在しない場合
    """
    base_dir = Path(__file__).parent.parent.parent
    font_dir = base_dir / "fonts/BIZ_UDMincho"

    # Phase 1の選定結果に基づき、.ttfファイルを検索
    # Regular/Boldどちらかが残っている前提
    candidates = list(font_dir.glob("*.ttf"))

    if not candidates:
        raise FileNotFoundError(
            f"Default font not found in {font_dir}\n"
            "Please ensure BIZ UDMincho font is installed or configure custom font in options['fonts']."
        )

    # 最初に見つかったフォントを使用
    return candidates[0]


def _register_font(font_path: Path | None = None) -> str:
    """
    TrueTypeフォントをReportLabに登録

    Args:
        font_path: フォントファイルのパス（Noneの場合はデフォルト使用）

    Returns:
        登録されたフォント名

    Raises:
        FileNotFoundError: フォントファイルが存在しない場合
    """
    if font_path is None:
        font_path = _find_default_font()

    if not font_path.exists():
        raise FileNotFoundError(
            f"Font file not found: {font_path}\n"
            "Please ensure the font file exists or configure custom font in options['fonts']."
        )

    # フォント名はファイル名から生成（拡張子除く）
    font_name = font_path.stem
    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    return font_name


def generate_resume_pdf(
    data: dict[str, Any],
    options: dict[str, Any],
    output_path: Path,
) -> None:
    """
    履歴書PDFを生成する（v3: 罫線+固定ラベル）

    Args:
        data: 履歴書データ（現在は未使用、将来的に記入済みデータ描画で使用）
        options: 生成オプション（paper_size, date_format, fonts等）
        output_path: 出力先PDFファイルパス
    """
    # レイアウトデータのJSONファイルパス（v3フォーマット）
    # TODO: options経由で指定できるようにする（A4/B5切り替え対応）
    layout_json_path = Path(__file__).parent.parent.parent / "data/layouts/resume_layout_a4_v2.json"

    with open(layout_json_path, encoding="utf-8") as f:
        layout_data = json.load(f)

    # A4サイズのCanvasを作成
    c = canvas.Canvas(str(output_path), pagesize=A4)

    # フォント登録（options['fonts']['main']を優先、未指定時はデフォルト）
    custom_font_path = None
    if "fonts" in options and "main" in options["fonts"]:
        custom_font_path = Path(options["fonts"]["main"])

    font_name = _register_font(custom_font_path)

    # Page 1: 罫線 + テキスト
    _draw_lines(c, layout_data["page1_lines"])
    if "page1_texts" in layout_data:  # v3フォーマット対応（後方互換性）
        _draw_texts(c, layout_data["page1_texts"], font_name)
    c.showPage()

    # Page 2: 罫線 + テキスト
    _draw_lines(c, layout_data["page2_lines"])
    if "page2_texts" in layout_data:
        _draw_texts(c, layout_data["page2_texts"], font_name)
    c.showPage()

    c.save()


def _draw_texts(
    c: canvas.Canvas,
    texts: list[dict[str, Any]],
    font_name: str,
) -> None:
    """
    固定テキストラベルを描画する（v3フォーマット対応）

    Args:
        c: ReportLabのCanvasオブジェクト
        texts: テキストデータのリスト（dict形式、v3フォーマット）
        font_name: 登録済みのフォント名
    """
    for text in texts:
        # フォント設定
        c.setFont(font_name, text["font_size"])

        # 色設定（黒固定）
        c.setFillColorRGB(0, 0, 0)

        # 配置方向に応じた描画
        align = text.get("align", "left")
        if align == "left":
            c.drawString(text["x"], text["y"], text["text"])
        elif align == "center":
            c.drawCentredString(text["x"], text["y"], text["text"])
        elif align == "right":
            c.drawRightString(text["x"], text["y"], text["text"])


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
