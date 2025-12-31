"""
PDF生成モジュールのテスト
"""

from pathlib import Path

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from skill.scripts.jtr.rirekisho_generator import generate_rirekisho_pdf


def test_generate_rirekisho_pdf_basic(tmp_path: Path) -> None:
    """
    基本的なPDF生成のテスト（罫線のみ）
    """
    output_path = tmp_path / "test_rirekisho.pdf"

    # 空のデータとオプションで生成
    data = {}
    options = {
        "paper_size": "A4",
        "date_format": "seireki",
    }

    generate_rirekisho_pdf(data, options, output_path)

    # PDFファイルが生成されたことを確認
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_rirekisho_pdf_creates_two_pages(tmp_path: Path) -> None:
    """
    2ページのPDFが生成されることを確認
    """
    output_path = tmp_path / "test_rirekisho_pages.pdf"

    data = {}
    options = {"paper_size": "A4"}

    generate_rirekisho_pdf(data, options, output_path)

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
    generate_rirekisho_pdf(data, options, output_path)

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
    options = {"paper_size": "A4", "fonts": {"mincho": str(custom_font)}}

    generate_rirekisho_pdf(data, options, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_font_not_found_error(tmp_path: Path) -> None:
    """存在しないフォントパス指定時にエラーが発生することを確認"""
    output_path = tmp_path / "test_font_error.pdf"

    data = {}
    options = {"paper_size": "A4", "fonts": {"mincho": "/nonexistent/path/to/font.ttf"}}

    with pytest.raises(FileNotFoundError):
        generate_rirekisho_pdf(data, options, output_path)


def test_layout_file_not_found_error(tmp_path: Path, monkeypatch) -> None:
    """レイアウトファイルが存在しない場合のエラーハンドリング"""
    output_path = tmp_path / "test_layout_error.pdf"

    # get_layout_pathをモックして存在しないパスを返す
    def mock_get_layout_path(*args, **kwargs):
        return tmp_path / "nonexistent_layout.json"

    monkeypatch.setattr(
        "skill.scripts.jtr.rirekisho_generator.get_layout_path", mock_get_layout_path
    )

    data = {}
    options = {"paper_size": "A4"}

    with pytest.raises(FileNotFoundError, match="レイアウトファイルが見つかりません"):
        generate_rirekisho_pdf(data, options, output_path)


def test_layout_file_invalid_json_error(tmp_path: Path, monkeypatch) -> None:
    """レイアウトファイルが不正なJSON形式の場合のエラーハンドリング"""
    output_path = tmp_path / "test_invalid_json.pdf"

    # 不正なJSONファイルを作成
    invalid_json_path = tmp_path / "invalid_layout.json"
    invalid_json_path.write_text("{ invalid json ]", encoding="utf-8")

    # get_layout_pathをモックして不正なJSONファイルを返す
    monkeypatch.setattr(
        "skill.scripts.jtr.rirekisho_generator.get_layout_path",
        lambda *args, **kwargs: invalid_json_path,
    )

    data = {}
    options = {"paper_size": "A4"}

    with pytest.raises(ValueError, match="レイアウトファイルの形式が不正です"):
        generate_rirekisho_pdf(data, options, output_path)


@pytest.mark.skipif(
    __import__("os").name == "nt", reason="Windowsではchmodでの読み取り禁止が保証されない"
)
def test_layout_file_permission_error(tmp_path: Path, monkeypatch) -> None:
    """レイアウトファイルの読み込み権限がない場合のエラーハンドリング"""
    import os

    output_path = tmp_path / "test_permission_error.pdf"

    # 読み取り権限のないファイルを作成
    no_read_path = tmp_path / "no_read_layout.json"
    no_read_path.write_text('{"test": "data"}', encoding="utf-8")
    os.chmod(no_read_path, 0o000)

    # chmod が機能しない環境（root等）ではスキップ
    if os.access(no_read_path, os.R_OK):
        os.chmod(no_read_path, 0o644)  # クリーンアップ
        pytest.skip("読み取り権限が落ちない環境のためスキップ")

    # get_layout_pathをモックして権限のないファイルを返す
    monkeypatch.setattr(
        "skill.scripts.jtr.rirekisho_generator.get_layout_path",
        lambda *args, **kwargs: no_read_path,
    )

    data = {}
    options = {"paper_size": "A4"}

    try:
        with pytest.raises(PermissionError, match="レイアウトファイルの読み込み権限がありません"):
            generate_rirekisho_pdf(data, options, output_path)
    finally:
        # クリーンアップ: 権限を戻してファイル削除できるようにする
        os.chmod(no_read_path, 0o644)
