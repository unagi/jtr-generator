"""フォント登録の共通化モジュール

pdf_generator.py と layout/metrics.py で重複していたフォント登録処理を統一します。
"""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_font(font_path: Path) -> str:
    """TrueTypeフォントをReportLabに登録

    Args:
        font_path: フォントファイルの絶対パス

    Returns:
        登録されたフォント名（ファイル名のstem）

    Raises:
        FileNotFoundError: フォントファイルが存在しない場合
    """
    if not font_path.exists():
        raise FileNotFoundError(f"フォントファイルが見つかりません: {font_path}")

    font_name = font_path.stem
    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    return font_name


def find_default_font() -> Path:
    """デフォルトフォント（BIZ UDMincho）のパスを取得

    Returns:
        デフォルトフォントの絶対パス

    Raises:
        FileNotFoundError: フォントファイルが存在しない場合
    """
    from .paths import get_assets_path

    font_dir = get_assets_path("fonts", "BIZ_UDMincho")

    # Phase 1の選定結果に基づき、.ttfファイルを検索
    # Regular/Boldどちらかが残っている前提
    candidates = list(font_dir.glob("*.ttf"))

    if not candidates:
        raise FileNotFoundError(
            f"デフォルトフォントが見つかりません: {font_dir}\n"
            "BIZ UDMinchoフォントがインストールされているか確認してください。"
        )

    return candidates[0]
