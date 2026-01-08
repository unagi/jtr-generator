"""
罫線のみの履歴書PDFを生成するテストスクリプト
"""

from pathlib import Path

from jtr.rirekisho_generator import generate_rirekisho_pdf

if __name__ == "__main__":
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "test_rirekisho_lines_only.pdf"

    # 空のデータとオプション
    data = {}
    options = {
        "paper_size": "A4",
        "date_format": "seireki",
    }

    print(f"Generating PDF: {output_path}")
    generate_rirekisho_pdf(data, options, output_path)
    print("✓ PDF generated successfully")
    print(f"  File size: {output_path.stat().st_size:,} bytes")
