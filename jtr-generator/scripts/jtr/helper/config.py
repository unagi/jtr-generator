"""設定ファイル読み込みとフォントパス解決"""

from pathlib import Path
from typing import Any

import yaml

from .paths import get_assets_path

DEFAULT_STYLE_COLORS = {
    "body_text": "#050315",
    "main": "#6761af",
    "sub": "#cdc69c",
    "accent": "#e36162",
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    config.yamlを読み込み

    Args:
        config_path: config.yamlのパス（Noneの場合はデフォルト設定を返す）

    Returns:
        設定辞書（date_format, paper_size, fonts, styles等）

    Raises:
        ValueError: config.yamlのパースエラー時
    """
    if config_path is None or not config_path.exists():
        # デフォルト設定を返す
        return {"options": {"date_format": "seireki", "paper_size": "A4"}, "fonts": {}}

    try:
        with open(config_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if not isinstance(loaded, dict):
                return {"options": {}, "fonts": {}}
            return loaded
    except yaml.YAMLError as e:
        raise ValueError(f"config.yamlの読み込みに失敗しました: {e}") from e


def resolve_font_paths(config: dict[str, Any]) -> dict[str, Any]:
    """
    相対パスを絶対パスに解決し、デフォルトフォントを設定

    Args:
        config: 設定辞書（相対パス含む）

    Returns:
        設定辞書（絶対パス、デフォルトフォント設定済み）

    Raises:
        FileNotFoundError: カスタムフォントファイルが存在しない場合
    """

    def resolve_font_key(fonts: dict[str, Any], key: str, label: str) -> None:
        if key not in fonts:
            return
        font_path = get_assets_path(fonts[key])
        if not font_path.exists():
            raise FileNotFoundError(
                f"{label}フォントファイルが見つかりません: {font_path}\n"
                f"config.yamlのfonts.{key}設定を確認してください。"
            )
        fonts[key] = str(font_path)

    # カスタムフォントが指定されている場合
    if "fonts" in config and config["fonts"]:
        fonts = config["fonts"]
        resolve_font_key(fonts, "mincho", "明朝")
        resolve_font_key(fonts, "gothic", "ゴシック")
    else:
        # デフォルトフォントを設定
        default_font_path = get_assets_path("fonts", "BIZ_UDMincho", "BIZUDMincho-Regular.ttf")
        if not default_font_path.exists():
            raise FileNotFoundError(
                f"デフォルトフォントが見つかりません: {default_font_path}\n"
                "BIZ UDMinchoフォントがインストールされているか確認してください。"
            )
        config["fonts"] = {"mincho": str(default_font_path)}

    return config


def resolve_style_colors(styles: dict[str, Any] | None) -> dict[str, str]:
    """スタイルカラー設定を解決（未指定はデフォルト）"""
    configured = {}
    if styles and isinstance(styles, dict):
        colors = styles.get("colors")
        if isinstance(colors, dict):
            configured = colors

    resolved: dict[str, str] = {}
    for key, fallback in DEFAULT_STYLE_COLORS.items():
        value = configured.get(key, fallback)
        resolved[key] = value if isinstance(value, str) and value else fallback
    return resolved
