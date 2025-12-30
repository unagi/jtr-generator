"""
PDF生成モジュールのテスト
"""

from pathlib import Path

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from skill.jtr.pdf_generator import generate_resume_pdf


def test_generate_resume_pdf_basic(tmp_path: Path) -> None:
    """
    基本的なPDF生成のテスト（罫線のみ）
    """
    output_path = tmp_path / "test_resume.pdf"

    # 空のデータとオプションで生成
    data = {}
    options = {
        "paper_size": "A4",
        "date_format": "seireki",
    }

    generate_resume_pdf(data, options, output_path)

    # PDFファイルが生成されたことを確認
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_resume_pdf_creates_two_pages(tmp_path: Path) -> None:
    """
    2ページのPDFが生成されることを確認
    """
    output_path = tmp_path / "test_resume_pages.pdf"

    data = {}
    options = {"paper_size": "A4"}

    generate_resume_pdf(data, options, output_path)

    # PDFファイルが生成されたことを確認
    assert output_path.exists()

    # pypdfを使ってページ数を確認
    import pypdf

    reader = pypdf.PdfReader(output_path)
    assert len(reader.pages) == 2


def test_default_font_registration(tmp_path: Path) -> None:
    """デフォルトフォントが正しく登録されることを確認"""
    output_path = tmp_path / "test_font_default.pdf"

    data = {}
    options = {"paper_size": "A4"}  # fonts指定なし

    # エラーが発生しないことを確認
    generate_resume_pdf(data, options, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_custom_font_registration(tmp_path: Path) -> None:
    """カスタムフォントが正しく登録されることを確認"""
    output_path = tmp_path / "test_font_custom.pdf"

    # Phase 5で削除されない方のフォントをカスタムとして指定
    # （この時点では両方あるので、どちらでもテスト可能）
    fonts_dir = Path(__file__).parent.parent.parent / "fonts/BIZ_UDMincho"
    custom_fonts = list(fonts_dir.glob("*.ttf"))

    if len(custom_fonts) < 1:
        pytest.skip("Custom font not available for testing")

    custom_font = custom_fonts[0]

    data = {}
    options = {"paper_size": "A4", "fonts": {"main": str(custom_font)}}

    generate_resume_pdf(data, options, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_font_not_found_error(tmp_path: Path) -> None:
    """存在しないフォントパス指定時にエラーが発生することを確認"""
    output_path = tmp_path / "test_font_error.pdf"

    data = {}
    options = {"paper_size": "A4", "fonts": {"main": "/nonexistent/path/to/font.ttf"}}

    with pytest.raises(FileNotFoundError):
        generate_resume_pdf(data, options, output_path)
