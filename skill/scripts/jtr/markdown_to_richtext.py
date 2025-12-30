"""Markdown to ReportLab Flowables converter

Markdownテキストをreportlab Flowablesに変換するモジュール。
職務経歴書PDF生成で使用。
"""

from __future__ import annotations

import re
from typing import Any

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer

__all__ = ["markdown_to_flowables"]


def markdown_to_flowables(
    markdown: str,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """
    Markdownテキストをreportlab Flowablesに変換

    対応するMarkdown構文:
    - 見出し: # H1, ## H2, ### H3, #### H4
    - 箇条書き: - item (行頭のみ)
    - 太字: **bold**
    - 段落: 空行で区切り

    Args:
        markdown: Markdown形式のテキスト
        styles: ParagraphStyleの辞書（"Heading1", "Heading2", "Heading3", "Heading4", "BodyText", "Bullet"を含む）

    Returns:
        reportlab Flowablesのリスト

    Raises:
        ValueError: 不正なMarkdown構文の場合
        KeyError: 必要なスタイルが存在しない場合
    """
    # 必須スタイルの存在確認
    required_styles = ["Heading1", "Heading2", "Heading3", "Heading4", "BodyText", "Bullet"]
    for style_name in required_styles:
        if style_name not in styles:
            raise KeyError(f"スタイル '{style_name}' が存在しません")

    flowables: list[Any] = []

    # 空のMarkdownは空リストを返す
    if not markdown.strip():
        return flowables

    lines = markdown.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # 空行 → スペーサー（ただし、最初と最後の空行はスキップ）
        if not line:
            # 既にflowablesがある場合のみスペーサーを追加
            if flowables:
                flowables.append(Spacer(1, 3 * mm))
            i += 1
            continue

        # 見出し（# H1, ## H2, ### H3, #### H4）
        if line.startswith("#"):
            heading_match = re.match(r"^(#{1,4})\s+(.*)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)

                # 太字をReportLab形式に変換
                text = _convert_bold(text)

                # スタイル選択
                if level == 1:
                    style = styles["Heading1"]
                elif level == 2:
                    style = styles["Heading2"]
                elif level == 3:
                    style = styles["Heading3"]
                else:  # level == 4
                    style = styles["Heading4"]

                flowables.append(Paragraph(text, style))
                flowables.append(Spacer(1, 2 * mm))
                i += 1
                continue

        # 箇条書き（行頭の "- "）
        if line.startswith("- "):
            bullet_text = line[2:]  # "- " を除去
            bullet_text = _convert_bold(bullet_text)
            flowables.append(Paragraph(f"• {bullet_text}", styles["Bullet"]))
            i += 1
            continue

        # 通常の段落
        # 複数行の段落を結合（次の空行・見出し・箇条書きまで）
        paragraph_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].rstrip()
            if not next_line or next_line.startswith("#") or next_line.startswith("- "):
                break
            paragraph_lines.append(next_line)
            i += 1

        paragraph_text = " ".join(paragraph_lines)
        paragraph_text = _convert_bold(paragraph_text)
        flowables.append(Paragraph(paragraph_text, styles["BodyText"]))

    return flowables


def _convert_bold(text: str) -> str:
    """
    Markdown太字 (**text**) をReportLab形式 (<b>text</b>) に変換

    Args:
        text: Markdown形式のテキスト

    Returns:
        ReportLab形式に変換されたテキスト
    """
    # **bold** → <b>bold</b>
    # 貪欲マッチを避けるため、非貪欲マッチ .*? を使用
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
