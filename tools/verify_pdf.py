"""
生成されたPDFの検証スクリプト
"""

from pathlib import Path

import pypdf

if __name__ == "__main__":
    pdf_path = Path("outputs/test_rirekisho_lines_only.pdf")

    if not pdf_path.exists():
        print(f"Error: {pdf_path} not found")
        exit(1)

    reader = pypdf.PdfReader(pdf_path)

    print(f"PDF: {pdf_path}")
    print(f"  Pages: {len(reader.pages)}")
    print(f"  Size: {pdf_path.stat().st_size:,} bytes")

    for i, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        print(f"  Page {i}: {width:.1f} x {height:.1f} pt")
        # A4 = 595.27 x 841.89 pt
        if abs(width - 595.27) < 1 and abs(height - 841.89) < 1:
            print("    → A4 size confirmed")
