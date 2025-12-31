"""Career Sheet (職務経歴書) PDF Generator

職務経歴書PDFを生成するモジュール。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .fonts import register_font
from .generation_context import get_generation_context, init_generation_context
from .markdown_to_richtext import HeadingBar, markdown_to_flowables
from .paths import get_assets_path

__all__ = ["generate_career_sheet_pdf"]

_DEFAULT_COLOR_TOKENS = {
    "body_text": "#050315",
    "main": "#6761af",
    "sub": "#cdc69c",
    "accent": "#e36162",
}

_PT_PER_MM = 72 / 25.4

_DEFAULT_SPACING_MM_VALUES: dict[str, float] = {
    "xs": 1.5,
    "sm": 2.0,
    "md": 3.0,
    "lg": 4.0,
    "xl": 6.0,
    "xxl": 8.0,
    "xxxl": 10.0,
}

_DEFAULT_SPACING_PT_VALUES: dict[str, float] = {
    "title_after": 5,
    "h1_before": 20,
    "h1_after": 10,
    "h2_before": 10,
    "h2_after": 3,
    "h2_rule_before": 1,
    "h2_rule_after": 3,
    "h3_before": 10,
    "h3_after": 9,
    "h4_before": 8,
    "h4_after": 7,
    "h5_before": 15,
    "h5_after": 5,
    "h6_before": 15,
    "h6_after": 3,
    "h7_before": 15,
    "h7_after": 1,
    "body_after": 3,
    "heading_bar_padding_x": 3 * _PT_PER_MM,
    "heading_bar_padding_y": 1.5 * _PT_PER_MM,
    "heading_bar_before": 17,
    "heading_bar_after": 6,
    "body_leading": 15,
}

_DEFAULT_INDENT_MM_VALUES: dict[str, float] = {
    "heading3": 2.0,
    "heading4": 4.0,
    "bullet_left": 8.0,
    "bullet_hanging": 3.0,
}


def _load_spacing_rules() -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    rules_path = get_assets_path("data", "a4", "rules", "career_sheet_spacing.json")
    spacing_mm = dict(_DEFAULT_SPACING_MM_VALUES)
    spacing_pt = dict(_DEFAULT_SPACING_PT_VALUES)
    indent_mm = dict(_DEFAULT_INDENT_MM_VALUES)

    if not rules_path.exists():
        return spacing_mm, spacing_pt, indent_mm

    try:
        with open(rules_path, encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError):
        return spacing_mm, spacing_pt, indent_mm

    if isinstance(loaded, dict):
        for key, value in loaded.get("spacing_mm", {}).items():
            if isinstance(value, (int, float)):
                spacing_mm[key] = float(value)
        for key, value in loaded.get("spacing_pt", {}).items():
            if isinstance(value, (int, float)):
                spacing_pt[key] = float(value)
        for key, value in loaded.get("indent_mm", {}).items():
            if isinstance(value, (int, float)):
                indent_mm[key] = float(value)

    return spacing_mm, spacing_pt, indent_mm


_SPACING_MM_VALUES, _SPACING_PT, _INDENT_MM_VALUES = _load_spacing_rules()
_SPACING_MM = {key: value * mm for key, value in _SPACING_MM_VALUES.items()}
_INDENT_MM = {key: value * mm for key, value in _INDENT_MM_VALUES.items()}
_BODY_LEADING_PT = _SPACING_PT.get("body_leading", _DEFAULT_SPACING_PT_VALUES["body_leading"])


def generate_career_sheet_pdf(
    resume_data: dict[str, Any],
    markdown_content: str,
    options: dict[str, Any],
    output_path: Path,
) -> None:
    """
    職務経歴書PDFを生成

    Args:
        resume_data: 履歴書データ（personal_info, qualificationsを使用）
        markdown_content: 職務経歴書本文（Markdown形式）
        options: 生成オプション（fonts等）
        output_path: 出力先PDFファイルパス

    Raises:
        FileNotFoundError: フォントファイルが見つからない場合
        ValueError: データ形式エラー
    """
    # フォント登録
    font_path = _resolve_career_sheet_font(options)
    if not font_path.exists():
        raise FileNotFoundError(f"フォントファイルが見つかりません: {font_path}")

    font_name = register_font(font_path)

    # PDFドキュメント作成
    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="default",
        leftPadding=0,
        rightPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])

    # スタイル作成
    color_palette = _resolve_color_palette(options)
    styles = _create_styles(font_name, color_palette)

    # Flowables作成
    flowables: list[Any] = []

    init_generation_context(options)

    # ヘッダー（個人情報・連絡先）
    flowables.extend(_create_header(resume_data, styles, color_palette))

    # 免許・資格（履歴書データから）
    if "qualifications" in resume_data and resume_data["qualifications"]:
        flowables.extend(
            _create_qualifications_section(resume_data["qualifications"], styles, color_palette)
        )

    # 本文（Markdown）
    decorations = {
        "heading2_bar": {
            "background": color_palette["main"],
            "padding_x": _SPACING_PT["heading_bar_padding_x"],
            "padding_y": _SPACING_PT["heading_bar_padding_y"],
            "space_before": _SPACING_PT["heading_bar_before"],
            "space_after": _SPACING_PT["heading_bar_after"],
        },
        "section_indent_step": _SPACING_MM["sm"],
        "heading2_rule": {
            "color": color_palette["sub"],
            "thickness": 0.6,
            "space_before": _SPACING_PT["h2_rule_before"],
            "space_after": _SPACING_PT["h2_rule_after"],
        },
        "thematic_break": {
            "color": color_palette["sub"],
            "thickness": 0.6,
            "space_before": _SPACING_PT["h2_rule_before"],
            "space_after": _SPACING_PT["h2_rule_after"],
        },
        "table": {
            "header_background": color_palette["sub"],
            "line_color": color_palette["sub"],
            "line_width": 0.5,
            "cell_padding": _SPACING_MM["sm"],
        },
        "code_block": {
            "background": color_palette["sub"],
            "left_indent": _SPACING_MM["sm"],
            "space_before": _SPACING_MM["sm"],
            "space_after": _SPACING_MM["sm"],
        },
        "blockquote": {
            "indent": _SPACING_MM["md"],
            "text_color": color_palette["body_text"],
        },
    }
    if markdown_content.strip():
        flowables.extend(_create_section_break(decorations["heading2_rule"]))
    flowables.extend(markdown_to_flowables(markdown_content, styles, decorations))

    # PDF生成
    doc.build(flowables)


def _resolve_color_palette(options: dict[str, Any]) -> dict[str, colors.Color]:
    """カラー設定を解決（未指定はデフォルト）"""
    configured = options.get("styles", {}).get("colors", {})
    palette: dict[str, colors.Color] = {}
    for key, fallback in _DEFAULT_COLOR_TOKENS.items():
        value = configured.get(key, fallback)
        if not isinstance(value, str) or not value:
            value = fallback
        palette[key] = colors.HexColor(value)
    return palette


def _create_styles(
    font_name: str,
    palette: dict[str, colors.Color],
) -> dict[str, ParagraphStyle]:
    """スタイルシート作成（視認性重視のデザイン）"""
    return {
        "Title": ParagraphStyle(
            "Title",
            fontName=font_name,
            fontSize=22,
            alignment=TA_CENTER,
            spaceAfter=_SPACING_PT["title_after"],
            textColor=palette["main"],
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            fontName=font_name,
            fontSize=13,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h1_after"],
            spaceBefore=_SPACING_PT["h1_before"],
            textColor=colors.white,
            backColor=palette["main"],
            # Note: borderWidth=0で下線効果は無効化、underlineProportionも効果なし
            # 将来的に下線を追加する場合はborderWidthを設定
            borderWidth=0,
            borderPadding=0,
            borderColor=palette["main"],
            leftIndent=0,
            underlineProportion=0.15,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            fontName=font_name,
            fontSize=14,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h2_after"],
            spaceBefore=_SPACING_PT["h2_before"],
            textColor=colors.white,
            leftIndent=0,
        ),
        "Heading3": ParagraphStyle(
            "Heading3",
            fontName=font_name,
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h3_after"],
            spaceBefore=_SPACING_PT["h3_before"],
            textColor=palette["body_text"],
            leftIndent=0,
        ),
        "Heading4": ParagraphStyle(
            "Heading4",
            fontName=font_name,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h4_after"],
            spaceBefore=_SPACING_PT["h4_before"],
            textColor=palette["main"],
            leftIndent=0,
        ),
        "Heading5": ParagraphStyle(
            "Heading5",
            fontName=font_name,
            fontSize=10.5,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h5_after"],
            spaceBefore=_SPACING_PT["h5_before"],
            textColor=palette["main"],
            leftIndent=0,
        ),
        "Heading6": ParagraphStyle(
            "Heading6",
            fontName=font_name,
            fontSize=10.5,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h6_after"],
            spaceBefore=_SPACING_PT["h6_before"],
            textColor=palette["main"],
            leftIndent=0,
        ),
        "Heading7": ParagraphStyle(
            "Heading7",
            fontName=font_name,
            fontSize=10.5,
            alignment=TA_LEFT,
            spaceAfter=_SPACING_PT["h7_after"],
            spaceBefore=_SPACING_PT["h7_before"],
            textColor=palette["main"],
            leftIndent=0,
        ),
        "BodyText": ParagraphStyle(
            "BodyText",
            fontName=font_name,
            fontSize=11,
            alignment=TA_LEFT,
            leading=_BODY_LEADING_PT,
            spaceAfter=_SPACING_PT["body_after"],
            textColor=palette["body_text"],
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            fontName=font_name,
            fontSize=11,
            alignment=TA_LEFT,
            leftIndent=_INDENT_MM["bullet_left"],
            firstLineIndent=-_INDENT_MM["bullet_hanging"],
            leading=15,
            spaceAfter=_SPACING_MM["xs"],
            textColor=palette["body_text"],
        ),
        "Header": ParagraphStyle(
            "Header",
            fontName=font_name,
            fontSize=9,
            alignment=TA_LEFT,
            textColor=palette["body_text"],
        ),
        "NameHeader": ParagraphStyle(
            "NameHeader",
            fontName=font_name,
            fontSize=16,
            alignment=TA_LEFT,
            textColor=palette["body_text"],
        ),
    }


def _create_header(
    resume_data: dict[str, Any],
    styles: dict[str, ParagraphStyle],
    palette: dict[str, colors.Color],
) -> list[Any]:
    """ヘッダー（個人情報・連絡先）作成（視認性重視）"""
    flowables: list[Any] = []

    # タイトル
    flowables.append(Paragraph("職務経歴書", styles["Title"]))

    # 日付（右寄せ、date_formatオプションに対応）
    from datetime import datetime

    now = datetime.now()
    date_formatter = get_generation_context().date_formatter
    date_text = f"{date_formatter.format(now.strftime('%Y-%m-%d'))} 現在"

    date_style = ParagraphStyle(
        "DateStyle",
        parent=styles["BodyText"],
        fontSize=9,
        alignment=TA_RIGHT,
    )
    flowables.append(Paragraph(date_text, date_style))
    flowables.append(Spacer(1, _SPACING_MM["sm"]))

    # 個人情報（氏名を強調）
    personal_info = resume_data.get("personal_info", {})
    name = personal_info.get("name", "")
    birthdate = date_formatter.format_or_raw(
        personal_info.get("birthdate", ""), format_style="full"
    )
    phone = personal_info.get("phone", "") or personal_info.get("mobile", "")
    email = personal_info.get("email", "")

    flowables.extend(_create_section_heading("プロフィール", styles, palette))

    # 連絡先情報をシンプルなテーブルで
    contact_data = [
        [f"氏名: {name}".strip(), f"電話: {phone}".strip()],
        [f"生年月日: {birthdate}".strip(), f"メール: {email}".strip()],
    ]

    contact_table = Table(
        contact_data,
        colWidths=[85 * mm, 85 * mm],
        rowHeights=[_SPACING_MM["xl"], _SPACING_MM["xl"]],
    )

    contact_table.setStyle(
        TableStyle(
            [
                (
                    "FONT",
                    (0, 0),
                    (-1, -1),
                    styles["BodyText"].fontName,
                    styles["BodyText"].fontSize,
                ),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TEXTCOLOR", (0, 0), (-1, -1), styles["BodyText"].textColor),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, palette["sub"]),
                ("LEFTPADDING", (0, 0), (-1, -1), _SPACING_MM["md"]),
                ("RIGHTPADDING", (0, 0), (-1, -1), _SPACING_MM["md"]),
                ("TOPPADDING", (0, 0), (-1, -1), _SPACING_MM["sm"]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), _SPACING_MM["sm"]),
            ]
        )
    )

    flowables.append(contact_table)
    flowables.append(Spacer(1, _SPACING_MM["xl"]))

    return flowables


def _create_qualifications_section(
    qualifications: list[dict[str, Any]],
    styles: dict[str, ParagraphStyle],
    palette: dict[str, colors.Color],
) -> list[Any]:
    """免許・資格セクション作成"""
    flowables: list[Any] = []

    flowables.extend(_create_section_heading("免許・資格", styles, palette))

    date_formatter = get_generation_context().date_formatter
    for qual in qualifications:
        date_str = date_formatter.format_or_raw(qual.get("date", ""), format_style="full")
        name = qual.get("name", "")
        flowables.append(Paragraph(f"• {date_str} {name}".strip(), styles["Bullet"]))

    flowables.append(Spacer(1, _SPACING_MM["xxl"]))

    return flowables


def _create_section_heading(
    title: str,
    styles: dict[str, ParagraphStyle],
    palette: dict[str, colors.Color],
) -> list[Any]:
    """共通セクション見出し（H2相当）"""
    flowables: list[Any] = []
    flowables.append(_create_heading_bar(title, styles, palette))
    return flowables


def _create_section_break(rule: dict[str, Any]) -> list[Any]:
    """構造データとMarkdownの間に入れる区切り線"""
    flowables: list[Any] = []
    flowables.append(
        HRFlowable(
            width="100%",
            thickness=float(rule.get("thickness", 0.6)),
            color=rule.get("color", colors.HexColor("#cdc69c")),
            spaceBefore=float(rule.get("space_before", _SPACING_MM["md"])),
            spaceAfter=float(rule.get("space_after", _SPACING_MM["md"])),
        )
    )
    return flowables


def _create_heading_bar(
    text: str,
    styles: dict[str, ParagraphStyle],
    palette: dict[str, colors.Color],
) -> HeadingBar:
    bar_style = ParagraphStyle(
        "Heading2Bar",
        parent=styles["Heading2"],
        spaceBefore=0,
        spaceAfter=0,
        leading=styles["Heading2"].fontSize,
    )
    return HeadingBar(
        text=text,
        style=bar_style,
        background=palette["main"],
        padding_x=_SPACING_PT["heading_bar_padding_x"],
        padding_y=_SPACING_PT["heading_bar_padding_y"],
        space_before=_SPACING_PT["heading_bar_before"],
        space_after=_SPACING_PT["heading_bar_after"],
    )


def _resolve_career_sheet_font(options: dict[str, Any]) -> Path:
    fonts = options.get("fonts", {})
    font_value = fonts.get("career_sheet_main") or fonts.get("main", "")
    return Path(font_value)
