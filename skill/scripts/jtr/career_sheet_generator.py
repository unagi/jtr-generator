"""Career Sheet (職務経歴書) PDF Generator

職務経歴書PDFを生成するモジュール。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .fonts import register_font
from .markdown_to_richtext import markdown_to_flowables

__all__ = ["generate_career_sheet_pdf"]


def generate_career_sheet_pdf(
    resume_data: dict[str, Any],
    markdown_content: str,
    additional_info: dict[str, Any],
    options: dict[str, Any],
    output_path: Path,
) -> None:
    """
    職務経歴書PDFを生成

    Args:
        resume_data: 履歴書データ（personal_info, qualificationsを使用）
        markdown_content: 職務経歴書本文（Markdown形式）
        additional_info: 追加情報（email等）
        options: 生成オプション（fonts等）
        output_path: 出力先PDFファイルパス

    Raises:
        FileNotFoundError: フォントファイルが見つからない場合
        ValueError: データ形式エラー
    """
    # フォント登録
    font_path = Path(options.get("fonts", {}).get("main", ""))
    if not font_path.exists():
        raise FileNotFoundError(f"フォントファイルが見つかりません: {font_path}")

    font_name = register_font(font_path)

    # PDFドキュメント作成
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    # スタイル作成
    styles = _create_styles(font_name)

    # Flowables作成
    flowables: list[Any] = []

    # ヘッダー（個人情報・連絡先）
    flowables.extend(_create_header(resume_data, additional_info, styles, options))

    # 免許・資格（履歴書データから）
    if "qualifications" in resume_data and resume_data["qualifications"]:
        flowables.extend(_create_qualifications_section(resume_data["qualifications"], styles))

    # 本文（Markdown）
    flowables.extend(markdown_to_flowables(markdown_content, styles))

    # PDF生成
    doc.build(flowables)


def _create_styles(font_name: str) -> dict[str, ParagraphStyle]:
    """スタイルシート作成（視認性重視のデザイン）"""
    return {
        "Title": ParagraphStyle(
            "Title",
            fontName=font_name,
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
            textColor=colors.HexColor("#1a365d"),
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            fontName=font_name,
            fontSize=16,
            alignment=TA_LEFT,
            spaceAfter=4 * mm,
            spaceBefore=6 * mm,
            textColor=colors.HexColor("#1a365d"),
            # Note: borderWidth=0で下線効果は無効化、underlineProportionも効果なし
            # 将来的に下線を追加する場合はborderWidthを設定
            borderWidth=0,
            borderPadding=0,
            borderColor=colors.HexColor("#1a365d"),
            leftIndent=0,
            underlineProportion=0.15,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            fontName=font_name,
            fontSize=13,
            alignment=TA_LEFT,
            spaceAfter=3 * mm,
            spaceBefore=4 * mm,
            textColor=colors.HexColor("#2c5282"),
            leftIndent=0,
        ),
        "Heading3": ParagraphStyle(
            "Heading3",
            fontName=font_name,
            fontSize=11.5,
            alignment=TA_LEFT,
            spaceAfter=2 * mm,
            spaceBefore=3 * mm,
            textColor=colors.HexColor("#4a5568"),
            leftIndent=2 * mm,
        ),
        "Heading4": ParagraphStyle(
            "Heading4",
            fontName=font_name,
            fontSize=10.5,
            alignment=TA_LEFT,
            spaceAfter=1.5 * mm,
            spaceBefore=2 * mm,
            textColor=colors.HexColor("#718096"),
            leftIndent=4 * mm,
        ),
        "BodyText": ParagraphStyle(
            "BodyText",
            fontName=font_name,
            fontSize=10,
            alignment=TA_LEFT,
            leading=15,
            spaceAfter=2 * mm,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            fontName=font_name,
            fontSize=10,
            alignment=TA_LEFT,
            leftIndent=8 * mm,
            leading=15,
            spaceAfter=1 * mm,
        ),
        "Header": ParagraphStyle(
            "Header",
            fontName=font_name,
            fontSize=9,
            alignment=TA_LEFT,
        ),
        "NameHeader": ParagraphStyle(
            "NameHeader",
            fontName=font_name,
            fontSize=16,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1a365d"),
        ),
    }


def _create_header(
    resume_data: dict[str, Any],
    additional_info: dict[str, Any],
    styles: dict[str, ParagraphStyle],
    options: dict[str, Any],
) -> list[Any]:
    """ヘッダー（個人情報・連絡先）作成（視認性重視）"""
    flowables: list[Any] = []

    # タイトル
    flowables.append(Paragraph("職務経歴書", styles["Title"]))

    # 日付（右寄せ、date_formatオプションに対応）
    from datetime import datetime

    from .japanese_era import convert_to_wareki

    now = datetime.now()
    date_format = options.get("date_format", "seireki")

    if date_format == "wareki":
        # 和暦変換
        date_text = f"{convert_to_wareki(now.strftime('%Y-%m-%d'))} 現在"
    else:
        # 西暦
        date_text = f"{now.year}年{now.month}月{now.day}日 現在"

    date_style = ParagraphStyle(
        "DateStyle",
        parent=styles["BodyText"],
        fontSize=9,
        alignment=TA_RIGHT,
    )
    flowables.append(Paragraph(date_text, date_style))
    flowables.append(Spacer(1, 6 * mm))

    # 個人情報（氏名を強調）
    personal_info = resume_data.get("personal_info", {})
    name = personal_info.get("name", "")
    birthdate = personal_info.get("birthdate", "")
    phone = personal_info.get("phone", "") or personal_info.get("mobile", "")
    email = additional_info.get("email", "")

    # 氏名を大きく表示
    flowables.append(Paragraph(name, styles["NameHeader"]))
    flowables.append(Spacer(1, 3 * mm))

    # 連絡先情報をシンプルなテーブルで
    contact_data = [
        ["生年月日", birthdate],
        ["電話", phone],
        ["メール", email],
    ]

    contact_table = Table(
        contact_data,
        colWidths=[25 * mm, 145 * mm],
        rowHeights=[6 * mm, 6 * mm, 6 * mm],
    )

    contact_table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), styles["Header"].fontName, 9),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4a5568")),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )

    flowables.append(contact_table)
    flowables.append(Spacer(1, 10 * mm))

    return flowables


def _create_qualifications_section(
    qualifications: list[dict[str, Any]],
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """免許・資格セクション作成"""
    flowables: list[Any] = []

    flowables.append(Paragraph("免許・資格", styles["Heading1"]))
    flowables.append(Spacer(1, 3 * mm))

    for qual in qualifications:
        date_str = qual.get("date", "")
        name = qual.get("name", "")
        flowables.append(Paragraph(f"{date_str} {name}", styles["BodyText"]))

    flowables.append(Spacer(1, 8 * mm))

    return flowables
