"""Tests for skill.scripts.jtr.markdown_to_richtext module"""

from __future__ import annotations

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Preformatted, Table

from skill.scripts.jtr.markdown_to_richtext import HeadingBar, markdown_to_flowables


@pytest.fixture
def sample_styles() -> dict[str, ParagraphStyle]:
    """テスト用スタイル定義"""
    return {
        "Heading2": ParagraphStyle("Heading2", fontSize=14, alignment=TA_LEFT),
        "Heading3": ParagraphStyle("Heading3", fontSize=12, alignment=TA_LEFT),
        "Heading4": ParagraphStyle("Heading4", fontSize=11, alignment=TA_LEFT),
        "BodyText": ParagraphStyle("BodyText", fontSize=10, alignment=TA_LEFT),
        "Bullet": ParagraphStyle("Bullet", fontSize=10, leftIndent=10, alignment=TA_LEFT),
    }


@pytest.fixture
def sample_decorations() -> dict[str, dict[str, object]]:
    """テスト用装飾定義"""
    return {
        "heading2_bar": {
            "background": "#1a365d",
            "padding_x": 2,
            "padding_y": 1,
        }
    }


class TestMarkdownToFlowables:
    """markdown_to_flowables関数のテスト"""

    def test_heading_conversion(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """見出しの変換テスト"""
        markdown = "# 見出し1\n\n## 見出し2\n\n### 見出し3"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 3

        # 見出し1
        assert isinstance(flowables[0], HeadingBar)

        # 見出し2
        assert isinstance(flowables[1], HeadingBar)

        # 見出し3
        assert isinstance(flowables[2], Paragraph)
        assert "見出し3" in flowables[2].text
        assert flowables[2].style.name == "Heading3"

    def test_heading4_conversion(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """H4見出しの変換テスト"""
        markdown = "#### 見出し4"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 1

        # 見出し4
        assert isinstance(flowables[0], Paragraph)
        assert "見出し4" in flowables[0].text
        assert flowables[0].style.name == "Heading4"

    def test_bullet_list_conversion(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """箇条書きの変換テスト"""
        markdown = "- 項目1\n- 項目2\n- 項目3"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 3

        for i, item in enumerate(flowables, 1):
            assert isinstance(item, Paragraph)
            assert f"項目{i}" in item.text
            assert item.text.startswith("• ")  # 箇条書き記号
            assert item.style.name == "Bullet"

    def test_bold_conversion(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """太字の変換テスト"""
        markdown = "これは**太字**のテストです。"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert "<b>太字</b>" in flowables[0].text

    def test_paragraph_multiline(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """複数行段落の結合テスト"""
        markdown = "これは1行目です。\nこれは2行目です。\nこれは3行目です。"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        # 複数行が空白で結合される
        assert "1行目" in flowables[0].text
        assert "2行目" in flowables[0].text
        assert "3行目" in flowables[0].text

    def test_empty_line_spacer(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """空行は段落区切りとして扱う"""
        markdown = "段落1\n\n段落2"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # 段落1 + 段落2
        assert len(flowables) == 2
        assert isinstance(flowables[0], Paragraph)
        assert isinstance(flowables[1], Paragraph)

    def test_mixed_content(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """見出し・箇条書き・段落の混在テスト"""
        markdown = """# タイトル

これは段落です。

## セクション

- 項目1
- 項目2

これは**太字**を含む段落です。"""

        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # タイトル見出し、段落、セクション見出し、箇条書き×2、段落など
        assert len(flowables) > 5

        # 最初の要素はタイトル
        assert isinstance(flowables[0], HeadingBar)

    def test_missing_style_error(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """必須スタイルが不足している場合のエラー"""
        incomplete_styles = {"Heading2": sample_styles["Heading2"]}  # 不完全なスタイル

        with pytest.raises(KeyError, match="スタイル"):
            markdown_to_flowables("# Test", incomplete_styles, sample_decorations)

    def test_empty_markdown(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """空のMarkdownの処理"""
        flowables = markdown_to_flowables("", sample_styles, sample_decorations)
        assert flowables == []

    def test_only_whitespace(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """空白のみのMarkdownの処理"""
        markdown = "\n\n\n"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # 空白のみ → 空リスト
        assert flowables == []

    def test_heading_with_multiple_spaces(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """複数スペースを含む見出しの処理"""
        markdown = "##  見出し"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 1
        assert isinstance(flowables[0], HeadingBar)

    def test_heading_without_space(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """スペースなしの見出し（無効）"""
        markdown = "#見出し"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # 見出しとして認識されず、通常の段落として扱われる
        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert flowables[0].style.name == "BodyText"

    def test_heading_with_indent(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """インデント付き見出し（CommonMark準拠）"""
        markdown = "   # 見出し"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # 先頭3スペースまで許容
        assert len(flowables) == 1
        assert isinstance(flowables[0], HeadingBar)

    def test_heading_with_too_much_indent(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """過剰インデント（4スペース以上は無効）"""
        markdown = "    # 見出し"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # 4スペース以上はコードブロック扱い
        assert len(flowables) == 1
        assert isinstance(flowables[0], Preformatted)

    def test_bold_with_unclosed_marker(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """未閉じの太字マーカー"""
        markdown = "これは**未閉じの太字です"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        # 閉じがない場合は変換されない
        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert "**" in flowables[0].text

    def test_thematic_break(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """水平線の変換テスト"""
        markdown = "----\n\n本文"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert isinstance(flowables[0], HRFlowable)
        assert isinstance(flowables[1], Paragraph)

    def test_table_conversion(
        self,
        sample_styles: dict[str, ParagraphStyle],
        sample_decorations: dict[str, dict[str, object]],
    ) -> None:
        """テーブルの変換テスト"""
        markdown = "| A | B |\n|---|---|\n| 1 | 2 |"
        flowables = markdown_to_flowables(markdown, sample_styles, sample_decorations)

        assert len(flowables) == 1
        assert isinstance(flowables[0], Table)
