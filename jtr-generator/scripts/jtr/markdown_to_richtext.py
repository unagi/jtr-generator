"""Markdown to ReportLab Flowables converter.

Mistune (GFMプラグイン) のASTをReportLab Flowablesに変換する。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Protocol, cast

import mistune
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Preformatted, Table, TableStyle
from reportlab.platypus import paragraph as paragraph_module

__all__ = ["HeadingBar", "markdown_to_flowables"]

_GFM_PLUGINS = ["strikethrough", "table", "task_lists", "url"]
_MARKDOWN = mistune.create_markdown(renderer="ast", plugins=_GFM_PLUGINS)


if TYPE_CHECKING:

    class FlowableBase(Protocol):
        width: float
        height: float
        spaceBefore: float
        spaceAfter: float
        keepWithNext: int
        canv: Any

        def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]: ...

        def draw(self) -> None: ...


else:
    from reportlab.platypus import Flowable as FlowableBase


class HeadingBar(FlowableBase):
    """Full-width heading bar with centered text."""

    canv: Any

    def __init__(
        self,
        text: str,
        style: ParagraphStyle,
        background: colors.Color,
        padding_x: float,
        padding_y: float,
        space_before: float,
        space_after: float,
    ) -> None:
        super().__init__()
        self.text = text
        self.style = style
        self.background = background
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.spaceBefore = space_before
        self.spaceAfter = space_after
        self.keepWithNext = 1
        self.canv = cast(Any, None)
        self._paragraph = Paragraph(self.text, self.style)
        self._paragraph_height = 0.0

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        inner_width = max(avail_width - 2 * self.padding_x, 0)
        self._paragraph = Paragraph(self.text, self.style)
        _, height = self._paragraph.wrap(inner_width, avail_height)
        self._paragraph_height = height
        self.width = avail_width
        self.height = height + 2 * self.padding_y
        return self.width, self.height

    def draw(self) -> None:
        self.canv.saveState()
        self.canv.setFillColor(self.background)
        self.canv.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        # Align text by glyph bounds, not the paragraph baseline.
        bl_para = getattr(self._paragraph, "blPara", None)
        if bl_para is None:
            y_offset = (self.height - self._paragraph_height) / 2
        else:
            ascent = float(getattr(bl_para, "ascent", self.style.fontSize))
            descent = float(getattr(bl_para, "descent", 0))
            line_count = max(len(getattr(bl_para, "lines", [])), 1)
            leading = float(getattr(self.style, "leading", self.style.fontSize))
            if paragraph_module.paraFontSizeHeightOffset:
                base_offset = self._paragraph_height - self.style.fontSize
            else:
                base_offset = self._paragraph_height - ascent
            block_center = base_offset + (ascent + descent) / 2 - (line_count - 1) * leading / 2
            y_offset = self.height / 2 - block_center
        self._paragraph.drawOn(self.canv, self.padding_x, y_offset)
        self.canv.restoreState()


class InsetFlowable(FlowableBase):
    """Flowable wrapper to apply left/right insets."""

    def __init__(self, flowable: FlowableBase, inset_left: float, inset_right: float) -> None:
        super().__init__()
        self.flowable = flowable
        self.inset_left = inset_left
        self.inset_right = inset_right
        self.spaceBefore = getattr(flowable, "spaceBefore", 0)
        self.spaceAfter = getattr(flowable, "spaceAfter", 0)
        self.keepWithNext = getattr(flowable, "keepWithNext", 0)
        self.canv = cast(Any, None)

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        inner_width = max(avail_width - self.inset_left - self.inset_right, 0)
        width, height = self.flowable.wrap(inner_width, avail_height)
        self.width = width + self.inset_left + self.inset_right
        self.height = height
        return self.width, self.height

    def split(self, avail_width: float, avail_height: float) -> list[Any]:
        inner_width = max(avail_width - self.inset_left - self.inset_right, 0)
        splitter = getattr(self.flowable, "split", None)
        if splitter is None:
            return []
        parts = splitter(inner_width, avail_height)
        return [InsetFlowable(part, self.inset_left, self.inset_right) for part in parts]

    def draw(self) -> None:
        self.canv.saveState()
        self.canv.translate(self.inset_left, 0)
        cast(Any, self.flowable).drawOn(self.canv, 0, 0)
        self.canv.restoreState()


def markdown_to_flowables(
    markdown: str,
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any] | None = None,
) -> list[Any]:
    """
    Markdownテキストをreportlab Flowablesに変換

    対応するMarkdown構文（GFMサブセット）:
    - 見出し: ## (H2), ### (H3), #### (H4) ※ # はH2扱い
    - 箇条書き: - item / タスク: - [x] item
    - 太字/斜体/取り消し線: **bold** / *italic* / ~~strike~~
    - 段落: 空行で区切り
    - 水平線: ---
    - コード: `code` / ```code```
    - テーブル: GFMテーブル

    Args:
        markdown: Markdown形式のテキスト
        styles: ParagraphStyleの辞書（"Heading2", "Heading3", "Heading4", "BodyText", "Bullet"を含む）

    Returns:
        reportlab Flowablesのリスト

    Raises:
        ValueError: 不正なMarkdown構文の場合
        KeyError: 必要なスタイルが存在しない場合
    """
    # 必須スタイルの存在確認
    required_styles = ["Heading2", "Heading3", "Heading4", "BodyText", "Bullet"]
    for style_name in required_styles:
        if style_name not in styles:
            raise KeyError(f"スタイル '{style_name}' が存在しません")

    flowables: list[Any] = []

    # 空のMarkdownは空リストを返す
    if not markdown.strip():
        return flowables

    decorations = decorations or {}
    tokens = cast(list[dict[str, Any]], _MARKDOWN(markdown))
    section_depth = 0
    section_indent_step = float(decorations.get("section_indent_step", 0))
    for token in tokens:
        section_depth = _append_block(
            token,
            flowables,
            styles,
            decorations,
            list_depth=0,
            section_depth=section_depth,
            section_indent_step=section_indent_step,
        )

    return flowables


def _append_block(
    token: dict[str, Any],
    flowables: list[Any],
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any],
    list_depth: int,
    section_depth: int,
    section_indent_step: float,
) -> int:
    token_type = token.get("type")
    if token_type in ("blank_line", None):
        return section_depth

    if token_type == "heading":
        level = int(token.get("attrs", {}).get("level", 2))
        text = _render_inline(token.get("children", []))
        if level <= 2:
            _append_h2_heading(text, flowables, styles, decorations)
            return 1
        heading_depth = max(level - 2, 0)
        heading_indent = heading_depth * section_indent_step
        if level == 3:
            heading = _build_paragraph(text, styles["Heading3"])
            _append_flowable(flowables, _wrap_inset(heading, heading_indent))
            return 2
        heading_style = _resolve_heading_style(styles, level)
        heading = _build_paragraph(text, heading_style)
        _append_flowable(flowables, _wrap_inset(heading, heading_indent))
        return min(level - 1, 6)

    if token_type == "paragraph":
        text = _render_inline(token.get("children", []))
        body = _build_paragraph(text, styles["BodyText"])
        _append_flowable(flowables, _wrap_inset(body, section_depth * section_indent_step))
        return section_depth

    if token_type == "list":
        _append_list(
            token,
            flowables,
            styles,
            decorations,
            list_depth,
            section_depth,
            section_indent_step,
        )
        return section_depth

    if token_type == "block_quote":
        _append_block_quote(
            token,
            flowables,
            styles,
            decorations,
            section_depth,
            section_indent_step,
        )
        return section_depth

    if token_type == "block_code":
        _append_block_code(
            token,
            flowables,
            styles,
            decorations,
            section_depth,
            section_indent_step,
        )
        return section_depth

    if token_type == "thematic_break":
        _append_rule(
            flowables,
            decorations.get("thematic_break", {}),
            section_depth,
            section_indent_step,
        )
        return section_depth

    if token_type == "table":
        _append_table(
            token,
            flowables,
            styles,
            decorations,
            section_depth,
            section_indent_step,
        )
        return section_depth
    return section_depth


def _append_h2_heading(
    text: str,
    flowables: list[Any],
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any],
) -> None:
    bar = decorations.get("heading2_bar")
    if bar:
        _append_flowable(flowables, _create_heading_bar(text, styles, bar))
        return
    para = _build_paragraph(text, styles["Heading2"])
    para.keepWithNext = 1
    _append_flowable(flowables, para)
    _append_rule(flowables, decorations.get("heading2_rule", {}), 0, 0)


def _append_rule(
    flowables: list[Any],
    rule: dict[str, Any],
    section_depth: int,
    section_indent_step: float,
) -> None:
    color = _resolve_color(rule.get("color"), colors.black)
    line = HRFlowable(
        width="100%",
        thickness=float(rule.get("thickness", 0.5)),
        color=color,
        spaceBefore=float(rule.get("space_before", 0)),
        spaceAfter=float(rule.get("space_after", 0)),
    )
    _append_flowable(flowables, _wrap_inset(line, section_depth * section_indent_step))


def _create_heading_bar(
    text: str,
    styles: dict[str, ParagraphStyle],
    bar: dict[str, Any],
) -> HeadingBar:
    background = _resolve_color(bar.get("background"), colors.black)
    padding_x = float(bar.get("padding_x", 0))
    padding_y = float(bar.get("padding_y", 0))
    return HeadingBar(
        text=text,
        style=styles["Heading2"],
        background=background,
        padding_x=padding_x,
        padding_y=padding_y,
        space_before=float(bar.get("space_before", 0)),
        space_after=float(bar.get("space_after", 0)),
    )


def _append_list(
    token: dict[str, Any],
    flowables: list[Any],
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any],
    list_depth: int,
    section_depth: int,
    section_indent_step: float,
) -> None:
    attrs = token.get("attrs", {})
    ordered = bool(attrs.get("ordered"))
    items = token.get("children", [])
    index = 1

    for item in items:
        item_type = item.get("type")
        if item_type not in ("list_item", "task_list_item"):
            continue
        bullet_text = _render_list_item(item)
        bullet_style = _bullet_style(styles["Bullet"], list_depth)
        if item_type == "task_list_item":
            checked = bool(item.get("attrs", {}).get("checked"))
            prefix = "[x]" if checked else "[ ]"
            bullet_text = f"{prefix} {bullet_text}".strip()
            bullet = _build_paragraph(f"• {bullet_text}", bullet_style)
            _append_flowable(flowables, _wrap_inset(bullet, section_depth * section_indent_step))
        else:
            if ordered:
                bullet = _build_paragraph(f"{index}. {bullet_text}", bullet_style)
                _append_flowable(
                    flowables, _wrap_inset(bullet, section_depth * section_indent_step)
                )
                index += 1
            else:
                bullet = _build_paragraph(f"• {bullet_text}", bullet_style)
                _append_flowable(
                    flowables, _wrap_inset(bullet, section_depth * section_indent_step)
                )

        for child in item.get("children", []):
            if child.get("type") == "list":
                _append_list(
                    child,
                    flowables,
                    styles,
                    decorations,
                    list_depth + 1,
                    section_depth,
                    section_indent_step,
                )


def _append_block_quote(
    token: dict[str, Any],
    flowables: list[Any],
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any],
    section_depth: int,
    section_indent_step: float,
) -> None:
    quote = decorations.get("blockquote", {})
    indent = float(quote.get("indent", 6 * mm))
    text_color = _resolve_color(quote.get("text_color"), styles["BodyText"].textColor)
    quote_style = ParagraphStyle(
        "BlockQuote",
        parent=styles["BodyText"],
        leftIndent=styles["BodyText"].leftIndent + indent,
        textColor=text_color,
    )
    for child in token.get("children", []):
        if child.get("type") == "paragraph":
            text = _render_inline(child.get("children", []))
            quote = _build_paragraph(text, quote_style)
            _append_flowable(flowables, _wrap_inset(quote, section_depth * section_indent_step))


def _append_block_code(
    token: dict[str, Any],
    flowables: list[Any],
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any],
    section_depth: int,
    section_indent_step: float,
) -> None:
    code = decorations.get("code_block", {})
    font_name = str(code.get("font_name", "Courier"))
    font_size = float(code.get("font_size", styles["BodyText"].fontSize))
    leading = float(code.get("leading", styles["BodyText"].leading))
    back_color = _resolve_color(code.get("background"), colors.white)
    left_indent = float(code.get("left_indent", styles["BodyText"].leftIndent))
    space_before = float(code.get("space_before", 0))
    space_after = float(code.get("space_after", 0))
    code_style = ParagraphStyle(
        "CodeBlock",
        fontName=font_name,
        fontSize=font_size,
        leading=leading,
        backColor=back_color,
        leftIndent=left_indent,
        spaceBefore=space_before,
        spaceAfter=space_after,
    )
    raw = token.get("raw", "")
    code_block = Preformatted(raw.rstrip("\n"), code_style)
    code_block.spaceBefore = code_style.spaceBefore
    code_block.spaceAfter = code_style.spaceAfter
    _append_flowable(flowables, _wrap_inset(code_block, section_depth * section_indent_step))


def _append_table(
    token: dict[str, Any],
    flowables: list[Any],
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, Any],
    section_depth: int,
    section_indent_step: float,
) -> None:
    header_rows: list[list[str]] = []
    body_rows: list[list[str]] = []
    for child in token.get("children", []):
        child_type = child.get("type")
        if child_type == "table_head":
            header_rows.extend(_extract_table_rows(child))
        elif child_type == "table_body":
            body_rows.extend(_extract_table_rows(child))

    rows = header_rows + body_rows
    if not rows:
        return

    table = Table(rows, hAlign="LEFT")
    table_style = _build_table_style(len(header_rows), styles["BodyText"], decorations)
    table.setStyle(table_style)
    _append_flowable(flowables, _wrap_inset(table, section_depth * section_indent_step))


def _extract_table_rows(token: dict[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    children = token.get("children", [])
    if children and children[0].get("type") == "table_cell":
        rows.append([_render_inline(cell.get("children", [])) for cell in children])
        return rows
    for row in children:
        if row.get("type") != "table_row":
            continue
        cells = [
            _render_inline(cell.get("children", []))
            for cell in row.get("children", [])
            if cell.get("type") == "table_cell"
        ]
        if cells:
            rows.append(cells)
    return rows


def _build_table_style(
    header_rows: int,
    base_style: ParagraphStyle,
    decorations: dict[str, Any],
) -> TableStyle:
    table = decorations.get("table", {})
    line_color = _resolve_color(table.get("line_color"), colors.black)
    header_background = _resolve_color(table.get("header_background"), colors.white)
    line_width = float(table.get("line_width", 0.5))
    cell_padding = float(table.get("cell_padding", 4))
    style_commands: list[tuple[Any, ...]] = [
        ("LINEBELOW", (0, 0), (-1, -1), line_width, line_color),
        ("LEFTPADDING", (0, 0), (-1, -1), cell_padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), cell_padding),
        ("TOPPADDING", (0, 0), (-1, -1), cell_padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), cell_padding),
        ("FONT", (0, 0), (-1, -1), base_style.fontName, base_style.fontSize),
    ]
    if header_rows > 0:
        style_commands.append(("BACKGROUND", (0, 0), (-1, header_rows - 1), header_background))
        style_commands.append(
            (
                "FONT",
                (0, 0),
                (-1, header_rows - 1),
                base_style.fontName,
                base_style.fontSize,
            )
        )
    return TableStyle(style_commands)


def _render_list_item(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for child in item.get("children", []):
        child_type = child.get("type")
        if child_type == "block_text":
            parts.append(_render_inline(child.get("children", [])))
        elif child_type == "paragraph":
            parts.append(_render_inline(child.get("children", [])))
    return " ".join([part for part in parts if part]).strip()


def _render_inline(tokens: Iterable[dict[str, Any]]) -> str:
    parts: list[str] = []
    for token in tokens:
        token_type = token.get("type")
        if token_type == "text":
            parts.append(_escape_text(token.get("raw", "")))
        elif token_type == "strong":
            parts.append(f"<b>{_render_inline(token.get('children', []))}</b>")
        elif token_type == "emphasis":
            parts.append(f"<i>{_render_inline(token.get('children', []))}</i>")
        elif token_type == "strikethrough":
            parts.append(f"<strike>{_render_inline(token.get('children', []))}</strike>")
        elif token_type == "codespan":
            code = _escape_text(token.get("raw", ""))
            parts.append(f'<font face="Courier">{code}</font>')
        elif token_type == "link":
            url = _escape_text(token.get("attrs", {}).get("url", ""))
            label = _render_inline(token.get("children", []))
            parts.append(f'<a href="{url}">{label}</a>')
        elif token_type == "image":
            alt = _escape_text(token.get("attrs", {}).get("alt", ""))
            if alt:
                parts.append(alt)
        elif token_type == "linebreak":
            parts.append("<br/>")
        elif token_type == "softbreak":
            parts.append(" ")
    return "".join(parts)


def _escape_text(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "")


def _resolve_color(value: Any, fallback: colors.Color) -> colors.Color:
    if isinstance(value, colors.Color):
        return value
    if isinstance(value, str) and value:
        return colors.HexColor(value)
    return fallback


def _bullet_style(base: ParagraphStyle, depth: int) -> ParagraphStyle:
    if depth <= 0:
        return base
    indent = base.leftIndent + depth * (4 * mm)
    hanging = base.firstLineIndent
    return ParagraphStyle(
        f"{base.name}Depth{depth}",
        parent=base,
        leftIndent=indent,
        firstLineIndent=hanging,
    )


def _resolve_heading_style(
    styles: dict[str, ParagraphStyle],
    level: int,
) -> ParagraphStyle:
    if level <= 4:
        return styles["Heading4"]
    style_name = f"Heading{level}"
    return styles.get(style_name, styles["Heading4"])


def _wrap_inset(flowable: FlowableBase, indent: float) -> FlowableBase:
    if indent <= 0:
        return flowable
    return InsetFlowable(flowable, indent, indent)


def _append_flowable(flowables: list[Any], flowable: FlowableBase) -> None:
    flowables.append(flowable)


def _build_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    paragraph = Paragraph(text, style)
    paragraph.spaceBefore = style.spaceBefore
    paragraph.spaceAfter = style.spaceAfter
    return paragraph
