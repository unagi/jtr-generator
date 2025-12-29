"""
罫線のみの履歴書PDFを生成するテストスクリプト
"""

from pathlib import Path

from src.generators.pdf import generate_resume_pdf

if __name__ == "__main__":
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "test_resume_lines_only.pdf"

    # 空のデータとオプション
    data = {}
    options = {
        "paper_size": "A4",
        "date_format": "seireki",
    }

    print(f"Generating PDF: {output_path}")
    generate_resume_pdf(data, options, output_path)
    print("✓ PDF generated successfully")
    print(f"  File size: {output_path.stat().st_size:,} bytes")
