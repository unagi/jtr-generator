"""Tests for skill.scripts.jtr.markdown_to_richtext module"""

from __future__ import annotations

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer

from skill.scripts.jtr.markdown_to_richtext import markdown_to_flowables


@pytest.fixture
def sample_styles() -> dict[str, ParagraphStyle]:
    """テスト用スタイル定義"""
    return {
        "Heading1": ParagraphStyle("Heading1", fontSize=16, alignment=TA_CENTER),
        "Heading2": ParagraphStyle("Heading2", fontSize=14, alignment=TA_LEFT),
        "Heading3": ParagraphStyle("Heading3", fontSize=12, alignment=TA_LEFT),
        "Heading4": ParagraphStyle("Heading4", fontSize=11, alignment=TA_LEFT),
        "BodyText": ParagraphStyle("BodyText", fontSize=10, alignment=TA_LEFT),
        "Bullet": ParagraphStyle("Bullet", fontSize=10, leftIndent=10, alignment=TA_LEFT),
    }


class TestMarkdownToFlowables:
    """markdown_to_flowables関数のテスト"""

    def test_heading_conversion(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """見出しの変換テスト"""
        markdown = "# 見出し1\n\n## 見出し2\n\n### 見出し3"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 見出し1 + 見出し後Spacer + 空行Spacer + 見出し2 + 見出し後Spacer + 空行Spacer + 見出し3 + 見出し後Spacer
        assert len(flowables) == 8

        # 見出し1
        assert isinstance(flowables[0], Paragraph)
        assert "見出し1" in flowables[0].text
        assert flowables[0].style.name == "Heading1"

        # 見出し1後のSpacer
        assert isinstance(flowables[1], Spacer)

        # 空行Spacer
        assert isinstance(flowables[2], Spacer)

        # 見出し2
        assert isinstance(flowables[3], Paragraph)
        assert "見出し2" in flowables[3].text
        assert flowables[3].style.name == "Heading2"

        # 見出し3
        assert isinstance(flowables[6], Paragraph)
        assert "見出し3" in flowables[6].text
        assert flowables[6].style.name == "Heading3"

    def test_heading4_conversion(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """H4見出しの変換テスト"""
        markdown = "#### 見出し4"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 見出し4 + 見出し後Spacer
        assert len(flowables) == 2

        # 見出し4
        assert isinstance(flowables[0], Paragraph)
        assert "見出し4" in flowables[0].text
        assert flowables[0].style.name == "Heading4"

        # 見出し4後のSpacer
        assert isinstance(flowables[1], Spacer)

    def test_bullet_list_conversion(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """箇条書きの変換テスト"""
        markdown = "- 項目1\n- 項目2\n- 項目3"
        flowables = markdown_to_flowables(markdown, sample_styles)

        assert len(flowables) == 3

        for i, item in enumerate(flowables, 1):
            assert isinstance(item, Paragraph)
            assert f"項目{i}" in item.text
            assert item.text.startswith("• ")  # 箇条書き記号
            assert item.style.name == "Bullet"

    def test_bold_conversion(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """太字の変換テスト"""
        markdown = "これは**太字**のテストです。"
        flowables = markdown_to_flowables(markdown, sample_styles)

        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert "<b>太字</b>" in flowables[0].text

    def test_paragraph_multiline(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """複数行段落の結合テスト"""
        markdown = "これは1行目です。\nこれは2行目です。\nこれは3行目です。"
        flowables = markdown_to_flowables(markdown, sample_styles)

        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        # 複数行が空白で結合される
        assert "1行目" in flowables[0].text
        assert "2行目" in flowables[0].text
        assert "3行目" in flowables[0].text

    def test_empty_line_spacer(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """空行がスペーサーに変換されることを確認"""
        markdown = "段落1\n\n段落2"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 段落1 + 空行スペーサー + 段落2
        assert len(flowables) == 3
        assert isinstance(flowables[0], Paragraph)
        assert isinstance(flowables[1], Spacer)
        assert isinstance(flowables[2], Paragraph)

    def test_mixed_content(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """見出し・箇条書き・段落の混在テスト"""
        markdown = """# タイトル

これは段落です。

## セクション

- 項目1
- 項目2

これは**太字**を含む段落です。"""

        flowables = markdown_to_flowables(markdown, sample_styles)

        # タイトル見出し、段落、セクション見出し、箇条書き×2、段落など
        assert len(flowables) > 5

        # 最初の要素はタイトル
        assert isinstance(flowables[0], Paragraph)
        assert "タイトル" in flowables[0].text
        assert flowables[0].style.name == "Heading1"

    def test_missing_style_error(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """必須スタイルが不足している場合のエラー"""
        incomplete_styles = {"Heading1": sample_styles["Heading1"]}  # 不完全なスタイル

        with pytest.raises(KeyError, match="スタイル"):
            markdown_to_flowables("# Test", incomplete_styles)

    def test_empty_markdown(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """空のMarkdownの処理"""
        flowables = markdown_to_flowables("", sample_styles)
        assert flowables == []

    def test_only_whitespace(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """空白のみのMarkdownの処理"""
        markdown = "\n\n\n"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 空白のみ → 空リスト
        assert flowables == []

    def test_heading_with_multiple_spaces(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """複数スペースを含む見出しの処理"""
        markdown = "##  見出し"
        flowables = markdown_to_flowables(markdown, sample_styles)

        assert len(flowables) == 2
        assert isinstance(flowables[0], Paragraph)
        # 余分なスペースは内部的に渡されるが、ReportLabが自動トリム
        assert "見出し" in flowables[0].text

    def test_heading_without_space(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """スペースなしの見出し（無効）"""
        markdown = "#見出し"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 見出しとして認識されず、通常の段落として扱われる
        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert flowables[0].style.name == "BodyText"

    def test_heading_with_indent(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """インデント付き見出し（CommonMark準拠）"""
        markdown = "   # 見出し"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 先頭3スペースまで許容
        assert len(flowables) == 2
        assert isinstance(flowables[0], Paragraph)
        assert flowables[0].style.name == "Heading1"

    def test_heading_with_too_much_indent(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """過剰インデント（4スペース以上は無効）"""
        markdown = "    # 見出し"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 見出しとして認識されず、通常の段落として扱われる
        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert flowables[0].style.name == "BodyText"

    def test_bold_with_unclosed_marker(self, sample_styles: dict[str, ParagraphStyle]) -> None:
        """未閉じの太字マーカー"""
        markdown = "これは**未閉じの太字です"
        flowables = markdown_to_flowables(markdown, sample_styles)

        # 閉じがない場合は変換されない
        assert len(flowables) == 1
        assert isinstance(flowables[0], Paragraph)
        assert "**" in flowables[0].text
