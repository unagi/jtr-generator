"""
参照PDFのページ2からテキスト位置を抽出

学歴・職歴セクションのデータフィールド座標を特定します。
"""

from pathlib import Path

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextBox, LTTextLine

    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False


def extract_text_with_positions(pdf_path):
    """PDFからテキストと座標を抽出（A3見開きの右半分 = page2相当）"""
    texts = []

    for page_num, page_layout in enumerate(extract_pages(pdf_path)):
        # A3サイズ: 1190.52 x 841.92 pt
        # 分割位置: x=595.26pt（中央）
        # page2 = 右半分（x > 595.26）

        print(f"Page {page_num + 1}: {page_layout.width:.2f} x {page_layout.height:.2f} pt")
        print()

        for element in page_layout:
            if isinstance(element, (LTTextBox, LTTextLine)):
                # 要素の座標
                x0, y0, x1, y1 = element.bbox
                text = element.get_text().strip()

                # page2相当（x > 595.26）のテキストのみ
                if x0 > 595.0 and text:
                    texts.append({
                        "text": text,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                    })

    return texts


def main():
    if not PDFMINER_AVAILABLE:
        print("Error: pdfminer.six is required")
        print("Install: pip install pdfminer.six")
        return

    base_dir = Path(__file__).parent.parent
    ref_pdf = base_dir / "tests/fixtures/R3_pdf_rirekisyo.pdf"

    if not ref_pdf.exists():
        print(f"Error: Reference PDF not found at {ref_pdf}")
        return

    # テキストと座標を抽出
    texts = extract_text_with_positions(ref_pdf)

    print("=== Page 2 (right half, x > 595.26) Text Elements ===")
    print(f"Total elements: {len(texts)}")
    print()

    # Y座標でソート（上から下へ）
    texts_sorted = sorted(texts, key=lambda t: -t["y1"])

    for item in texts_sorted[:50]:  # 上位50要素を表示
        print(f"y={item['y1']:.2f}, x={item['x0']:.2f}: {item['text'][:60]}")


if __name__ == "__main__":
    main()
