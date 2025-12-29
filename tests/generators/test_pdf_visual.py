"""
PDF視覚的品質検証テスト

このテストは以下を検証します:
1. 参照PDFとの視覚的類似性（ピクセル差異率 < 1%）
2. 構造類似度（SSIM > 0.99）
3. デバッグ用の差分画像保存

注意: このテストはpdf2image（poppler-utils）に依存します
"""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from skimage.metrics import structural_similarity as ssim

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from src.generators.pdf import generate_resume_pdf

# pdf2imageが利用できない場合はテストをスキップ
pytestmark = pytest.mark.skipif(
    not PDF2IMAGE_AVAILABLE, reason="pdf2image not available (requires poppler-utils)"
)


@pytest.fixture
def generated_pdf_path(tmp_path):
    """テスト用のPDFを生成"""
    output_path = tmp_path / "test_resume.pdf"
    generate_resume_pdf({}, {"paper_size": "A4"}, output_path)
    return output_path


@pytest.fixture
def reference_pdf_path():
    """参照PDFのパス"""
    return Path(__file__).parent.parent / "fixtures/R3_pdf_rirekisyo.pdf"


def _pdf_to_images(pdf_path: Path, dpi: int = 300) -> list[Image.Image]:
    """PDFを画像に変換（poppler-utils必須）"""
    try:
        return convert_from_path(pdf_path, dpi=dpi)
    except Exception as exc:
        pytest.skip(f"pdf2image conversion failed (poppler-utils required): {exc}")


def _split_a3_to_a4(a3_image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """A3横画像を中央で分割してA4 x 2に変換"""
    width, height = a3_image.size
    mid = width // 2

    page1 = a3_image.crop((0, 0, mid, height))
    page2 = a3_image.crop((mid, 0, width, height))

    return page1, page2


def _calculate_pixel_diff_rate(img1: Image.Image, img2: Image.Image, threshold: int = 5) -> float:
    """
    2つの画像のピクセル単位差異率を計算

    Args:
        img1: 参照画像
        img2: 比較画像
        threshold: 差異の閾値（この値未満の差異は無視）

    Returns:
        差異率（0.0 = 完全一致、1.0 = 完全不一致）
    """
    # サイズが一致しない場合はリサイズ
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    # グレースケール化（罫線のみなので色情報は不要）
    arr1 = np.array(img1.convert("L"))
    arr2 = np.array(img2.convert("L"))

    # 差分の絶対値
    diff = np.abs(arr1.astype(float) - arr2.astype(float))

    # アンチエイリアシング対策: threshold未満の差異は無視
    diff[diff < threshold] = 0

    # 差異率の計算
    total_pixels = arr1.size
    diff_pixels = np.count_nonzero(diff)

    return diff_pixels / total_pixels


def _calculate_ssim(img1: Image.Image, img2: Image.Image) -> float:
    """
    2つの画像のSSIM（構造類似度）を計算

    Args:
        img1: 参照画像
        img2: 比較画像

    Returns:
        SSIM値（1.0 = 完全一致、0.0 = 完全不一致）
    """
    # サイズ統一
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    # グレースケール化
    arr1 = np.array(img1.convert("L"))
    arr2 = np.array(img2.convert("L"))

    # SSIM計算
    return ssim(arr1, arr2, data_range=255)


def test_visual_similarity_with_reference_pdf(generated_pdf_path, reference_pdf_path):
    """生成PDFと参照PDFの視覚的類似性を確認（ピクセル差異率 < 1%）"""
    # PDFを画像に変換（300dpi）
    reference_images = _pdf_to_images(reference_pdf_path, dpi=300)
    generated_images = _pdf_to_images(generated_pdf_path, dpi=300)

    # 参照PDF（A3横）を中央で分割してA4 x 2に変換
    assert len(reference_images) == 1, "Reference PDF should have 1 page (A3)"
    ref_page1, ref_page2 = _split_a3_to_a4(reference_images[0])

    # 生成PDF（A4 x 2）
    assert len(generated_images) >= 2, "Generated PDF should have at least 2 pages"
    gen_page1 = generated_images[0]
    gen_page2 = generated_images[1]

    # ページ1の比較
    diff_rate_1 = _calculate_pixel_diff_rate(ref_page1, gen_page1, threshold=5)
    print(f"\nPage 1 pixel difference rate: {diff_rate_1:.4f} ({diff_rate_1 * 100:.2f}%)")

    # ページ2の比較
    diff_rate_2 = _calculate_pixel_diff_rate(ref_page2, gen_page2, threshold=5)
    print(f"Page 2 pixel difference rate: {diff_rate_2:.4f} ({diff_rate_2 * 100:.2f}%)")

    # 閾値チェック（1%未満）
    assert diff_rate_1 < 0.01, f"Page 1 diff rate {diff_rate_1:.4f} exceeds 1% threshold"
    assert diff_rate_2 < 0.01, f"Page 2 diff rate {diff_rate_2:.4f} exceeds 1% threshold"


def test_structural_similarity_ssim(generated_pdf_path, reference_pdf_path):
    """SSIMで構造的類似性を評価（SSIM > 0.99）"""
    # PDFを画像に変換（300dpi）
    reference_images = _pdf_to_images(reference_pdf_path, dpi=300)
    generated_images = _pdf_to_images(generated_pdf_path, dpi=300)

    # A3を分割
    ref_page1, ref_page2 = _split_a3_to_a4(reference_images[0])
    gen_page1 = generated_images[0]
    gen_page2 = generated_images[1]

    # SSIM計算（ページ1）
    ssim_1 = _calculate_ssim(ref_page1, gen_page1)
    print(f"\nPage 1 SSIM: {ssim_1:.6f}")

    # SSIM計算（ページ2）
    ssim_2 = _calculate_ssim(ref_page2, gen_page2)
    print(f"Page 2 SSIM: {ssim_2:.6f}")

    # 閾値チェック（0.99以上）
    assert ssim_1 > 0.99, f"Page 1 SSIM {ssim_1:.6f} below 0.99 threshold"
    assert ssim_2 > 0.99, f"Page 2 SSIM {ssim_2:.6f} below 0.99 threshold"


@pytest.mark.skip(reason="Debug test - manually enable when needed")
def test_save_diff_image_for_debugging(generated_pdf_path, reference_pdf_path, tmp_path):
    """
    テスト失敗時のデバッグ用に差分画像を保存
    （このテストは通常スキップされ、手動で有効化した場合のみ実行）
    """
    # PDFを画像に変換
    reference_images = _pdf_to_images(reference_pdf_path, dpi=300)
    generated_images = _pdf_to_images(generated_pdf_path, dpi=300)

    # A3を分割
    ref_page1, ref_page2 = _split_a3_to_a4(reference_images[0])
    gen_page1 = generated_images[0]
    gen_page2 = generated_images[1]

    # デバッグディレクトリを作成
    debug_dir = Path(__file__).parent.parent.parent / "outputs/debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    # ページ1の差分画像を生成
    arr1 = np.array(ref_page1.convert("L"))
    arr2 = np.array(gen_page1.convert("L"))

    if arr1.shape != arr2.shape:
        arr2 = np.array(gen_page1.resize(ref_page1.size, Image.LANCZOS).convert("L"))

    diff = np.abs(arr1.astype(float) - arr2.astype(float))

    # 差分を強調表示（0-255の範囲に正規化）
    diff_normalized = (
        (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)
    )
    diff_img = Image.fromarray(diff_normalized)

    # 差分画像を保存
    diff_img.save(debug_dir / "diff_page1.png")
    ref_page1.save(debug_dir / "ref_page1.png")
    gen_page1.save(debug_dir / "gen_page1.png")

    # ページ2の差分画像を生成
    arr1 = np.array(ref_page2.convert("L"))
    arr2 = np.array(gen_page2.convert("L"))

    if arr1.shape != arr2.shape:
        arr2 = np.array(gen_page2.resize(ref_page2.size, Image.LANCZOS).convert("L"))

    diff = np.abs(arr1.astype(float) - arr2.astype(float))
    diff_normalized = (
        (diff / diff.max() * 255).astype(np.uint8) if diff.max() > 0 else diff.astype(np.uint8)
    )
    diff_img = Image.fromarray(diff_normalized)

    diff_img.save(debug_dir / "diff_page2.png")
    ref_page2.save(debug_dir / "ref_page2.png")
    gen_page2.save(debug_dir / "gen_page2.png")

    print(f"\nDebug images saved to: {debug_dir}")


def test_generated_pdf_basic_properties(generated_pdf_path):
    """生成されたPDFの基本的なプロパティを確認"""
    assert generated_pdf_path.exists(), "Generated PDF should exist"
    assert generated_pdf_path.stat().st_size > 0, "Generated PDF should not be empty"

    # 画像変換できることを確認
    images = _pdf_to_images(generated_pdf_path, dpi=72)
    assert len(images) == 2, "Generated PDF should have 2 pages"
