"""
セル単位でのPDF比較ツール

特定のセル領域を切り抜いて、参照PDFと生成PDFの視覚的類似性を測定します。
罫線の影響を排除し、セル内テキストの配置精度を正確に評価できます。
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not available (requires poppler-utils)")


def _split_a3_to_a4(a3_image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """A3横画像を中央で分割してA4 x 2に変換"""
    width, height = a3_image.size
    mid = width // 2

    page1 = a3_image.crop((0, 0, mid, height))
    page2 = a3_image.crop((mid, 0, width, height))

    return page1, page2


def compare_cell_region(
    ref_image: Image.Image,
    gen_image: Image.Image,
    cell_bbox: tuple[int, int, int, int],
    cell_name: str,
    output_dir: Path,
) -> dict:
    """
    指定セル領域の視覚的類似性を測定

    Args:
        ref_image: 参照画像（A4サイズ）
        gen_image: 生成画像（A4サイズ）
        cell_bbox: セルの境界ボックス (x0, y0, x1, y1) ピクセル座標
        cell_name: セルの識別名（保存ファイル名用）
        output_dir: デバッグ画像の保存先

    Returns:
        {
            "cell_name": str,
            "ssim": float,
            "pixel_diff_rate": float,
            "needs_review": bool
        }
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # セルを切り抜き
    ref_cell = ref_image.crop(cell_bbox)
    gen_cell = gen_image.crop(cell_bbox)

    # サイズ統一（念のため）
    if ref_cell.size != gen_cell.size:
        gen_cell = gen_cell.resize(ref_cell.size, Image.LANCZOS)

    # グレースケール化
    ref_arr = np.array(ref_cell.convert("L"))
    gen_arr = np.array(gen_cell.convert("L"))

    # SSIM計算
    ssim_score = ssim(ref_arr, gen_arr, data_range=255)

    # ピクセル差異率（threshold=5）
    diff = np.abs(ref_arr.astype(float) - gen_arr.astype(float))
    diff[diff < 5] = 0
    pixel_diff_rate = np.count_nonzero(diff) / ref_arr.size

    # デバッグ画像を保存
    ref_cell.save(output_dir / f"{cell_name}_ref.png")
    gen_cell.save(output_dir / f"{cell_name}_gen.png")

    # 差分画像
    diff_normalized = (
        (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)
    )
    diff_img = Image.fromarray(diff_normalized)
    diff_img.save(output_dir / f"{cell_name}_diff.png")

    return {
        "cell_name": cell_name,
        "ssim": float(ssim_score),
        "pixel_diff_rate": float(pixel_diff_rate),
        "needs_review": bool(ssim_score < 0.95 or pixel_diff_rate > 0.05),
    }


def load_critical_cells() -> dict:
    """
    重要セルの定義を読み込み

    Returns:
        {
            "page1": [
                {"name": "...", "bbox_px": (x0, y0, x1, y1), "description": "..."},
                ...
            ],
            "page2": [...]
        }
    """
    base_dir = Path(__file__).parent.parent
    cells_json = base_dir / "data/critical_cells.json"

    with open(cells_json, encoding="utf-8") as f:
        cells = json.load(f)

    # bbox_px形式に統一
    for page_cells in cells.values():
        for cell in page_cells:
            cell["bbox"] = cell["bbox_px"]

    return cells


def main():
    """メイン処理: セル単位比較の実行"""
    if not PDF2IMAGE_AVAILABLE:
        print("Error: pdf2image is required for this tool")
        print("Install: pip install pdf2image")
        print("Also requires: poppler-utils (system package)")
        return

    base_dir = Path(__file__).parent.parent
    ref_pdf = base_dir / "tests/fixtures/R3_pdf_rirekisyo.pdf"
    gen_pdf = base_dir / "outputs/test_resume.pdf"

    # 生成PDFを作成（最新のレイアウトで）
    print("Generating test PDF with current layout...")
    from src.generators.pdf import generate_resume_pdf

    generate_resume_pdf({}, {"paper_size": "A4"}, gen_pdf)

    # PDFを画像に変換（300dpi）
    print("Converting PDFs to images (300dpi)...")
    ref_images = convert_from_path(ref_pdf, dpi=300)
    gen_images = convert_from_path(gen_pdf, dpi=300)

    # A3を分割
    ref_page1, _ref_page2 = _split_a3_to_a4(ref_images[0])
    gen_page1 = gen_images[0]
    _gen_page2 = gen_images[1]

    # 重要セルの定義を読み込み
    critical_cells = load_critical_cells()

    # 出力ディレクトリ
    output_dir = base_dir / "outputs/debug/cells"

    # Page 1のセルを比較
    print("\n=== Page 1 Cell Comparison ===")
    results = []
    for cell_def in critical_cells["page1"]:
        print(f"\nAnalyzing: {cell_def['name']} - {cell_def['description']}")
        result = compare_cell_region(
            ref_page1, gen_page1, cell_def["bbox"], cell_def["name"], output_dir
        )
        result["description"] = cell_def["description"]
        results.append(result)

        print(f"  SSIM: {result['ssim']:.6f}")
        print(f"  Pixel Diff: {result['pixel_diff_rate']:.4f} ({result['pixel_diff_rate'] * 100:.2f}%)")
        print(f"  Needs Review: {'⚠️ YES' if result['needs_review'] else '✅ NO'}")

    # 結果をJSONで保存
    result_json = base_dir / "outputs/debug/cell_comparison_results.json"
    with open(result_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\nResults saved to: {result_json}")
    print(f"Cell images saved to: {output_dir}")

    # レビューが必要なセルをサマリー
    needs_review = [r for r in results if r["needs_review"]]
    if needs_review:
        print("\n⚠️  Cells requiring text extraction:")
        for r in needs_review:
            print(f"  - {r['cell_name']}: SSIM {r['ssim']:.4f}, Diff {r['pixel_diff_rate']:.2%}")
    else:
        print("\n✅ All cells look good!")


if __name__ == "__main__":
    main()
