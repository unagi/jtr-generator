"""
セル座標の測定ツール

参照画像から重要セルの座標を目視+計算で特定します。
"""

from pathlib import Path

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


def main():
    if not PDF2IMAGE_AVAILABLE:
        print("Error: pdf2image is required")
        return

    base_dir = Path(__file__).parent.parent
    ref_pdf = base_dir / "tests/fixtures/R3_pdf_rirekisyo.pdf"

    # PDFを画像に変換（300dpi）
    print("Converting reference PDF to image (300dpi)...")
    ref_images = convert_from_path(ref_pdf, dpi=300)
    ref_a3 = ref_images[0]

    # A3サイズ（1190.52 x 841.92 pt）→ 300dpi変換
    # 横幅: 1190.52 * (300/72) = 4960.5 px
    # 高さ: 841.92 * (300/72) = 3508 px
    print(f"\nA3 Image Size: {ref_a3.size}")

    # 中央で分割
    width, height = ref_a3.size
    mid = width // 2
    print(f"Split at: {mid} px")

    page1 = ref_a3.crop((0, 0, mid, height))
    print(f"Page 1 Size: {page1.size}")

    # Page 1を保存（座標測定用）
    debug_dir = base_dir / "outputs/debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    page1.save(debug_dir / "ref_page1_fullsize.png")
    print(f"\nSaved: {debug_dir / 'ref_page1_fullsize.png'}")
    print("Use this image to measure cell coordinates visually.")

    # 既知の情報から主要な境界を推定
    # A4サイズ: 595.26 x 841.92 pt → 2481 x 3508 px (300dpi)
    print("\n=== Key Landmarks (estimated) ===")
    print("Page width: 2481 px")
    print("Page height: 3508 px")

    # 履歴書タイトル行の下端（"年月日現在"の行）: 約y=150px
    # 氏名欄の下端: 約y=320px
    # 生年月日・年齢行の下端: 約y=480px
    # 現住所欄の下端: 約y=680px
    # 連絡先欄の下端: 約y=880px
    # 学歴欄の開始: 約y=950px

    # 写真エリア: 右上、氏名欄の右側
    # 推定: x=1800-2450, y=150-800

    print("\n=== Critical Cells (manual measurement required) ===")
    print("1. Photo Area (写真をはる位置)")
    print("   - Location: Top-right of page 1")
    print("   - Rough estimate: x=1800-2450, y=150-800")
    print("   - Please measure exact coordinates from ref_page1_fullsize.png")
    print()
    print("2. Age Cell (年月日生（満　歳）)")
    print("   - Location: Row below name field")
    print("   - Contains: '年　　　月　　　日生　　（満　　歳）'")
    print("   - Rough estimate: x=100-2450, y=320-480")
    print()
    print("3. Note Cell (※「性別」欄の注記)")
    print("   - Location: Bottom of page 1")
    print("   - Contains: '※「性別」欄：記載は任意です。本記載とすることも可能です。'")
    print("   - Rough estimate: x=100-2450, y=3400-3500")


if __name__ == "__main__":
    main()
