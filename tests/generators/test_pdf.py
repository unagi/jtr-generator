"""
PDF生成モジュールのテスト
"""

from pathlib import Path

from src.generators.pdf import generate_resume_pdf


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
