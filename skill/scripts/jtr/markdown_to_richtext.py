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
        # CommonMark準拠: 先頭3スペースまでのインデント許容
        stripped = line.lstrip(" ")
        indent_len = len(line) - len(stripped)

        if indent_len <= 3 and stripped.startswith("#"):
            # #の連続をカウント
            hash_count = 0
            for char in stripped:
                if char == "#":
                    hash_count += 1
                else:
                    break

            # H1-H4の範囲チェック
            if 1 <= hash_count <= 4 and len(stripped) > hash_count:
                # #の後の文字がスペースまたはタブかチェック
                next_char = stripped[hash_count]
                if next_char in (" ", "\t"):
                    text = stripped[hash_count + 1:]

                    # 太字をReportLab形式に変換
                    text = _convert_bold(text)

                    # スタイル選択
                    if hash_count == 1:
                        style = styles["Heading1"]
                    elif hash_count == 2:
                        style = styles["Heading2"]
                    elif hash_count == 3:
                        style = styles["Heading3"]
                    else:  # hash_count == 4
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
    # ReDoS対策: 正規表現を使わず、文字列パースで実装
    result = []
    i = 0
    while i < len(text):
        if i < len(text) - 3 and text[i:i+2] == "**":
            # 閉じの ** を探す
            end = text.find("**", i + 2)
            if end != -1:
                # 太字として変換
                result.append("<b>")
                result.append(text[i+2:end])
                result.append("</b>")
                i = end + 2
            else:
                # 閉じがない場合はそのまま
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)
