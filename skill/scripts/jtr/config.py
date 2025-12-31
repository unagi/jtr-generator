"""設定ファイル読み込みとフォントパス解決"""

from pathlib import Path
from typing import Any

import yaml

from .paths import get_assets_path


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
    # カスタムフォントが指定されている場合
    if "fonts" in config and config["fonts"]:
        if "main" in config["fonts"]:
            # config.yaml内のパスは assets/ からの相対パスとして解決
            custom_font_path = get_assets_path(config["fonts"]["main"])
            if not custom_font_path.exists():
                raise FileNotFoundError(
                    f"カスタムフォントファイルが見つかりません: {custom_font_path}\n"
                    "config.yamlのfonts.main設定を確認してください。"
                )
            config["fonts"]["main"] = str(custom_font_path)

        if "career_sheet_main" in config["fonts"]:
            career_font_path = get_assets_path(config["fonts"]["career_sheet_main"])
            if not career_font_path.exists():
                raise FileNotFoundError(
                    f"職務経歴書フォントファイルが見つかりません: {career_font_path}\n"
                    "config.yamlのfonts.career_sheet_main設定を確認してください。"
                )
            config["fonts"]["career_sheet_main"] = str(career_font_path)

        if "heading" in config["fonts"]:
            heading_font_path = get_assets_path(config["fonts"]["heading"])
            if not heading_font_path.exists():
                raise FileNotFoundError(
                    f"見出しフォントファイルが見つかりません: {heading_font_path}\n"
                    "config.yamlのfonts.heading設定を確認してください。"
                )
            config["fonts"]["heading"] = str(heading_font_path)
    else:
        # デフォルトフォントを設定
        default_font_path = get_assets_path("fonts", "BIZ_UDMincho", "BIZUDMincho-Regular.ttf")
        if not default_font_path.exists():
            raise FileNotFoundError(
                f"デフォルトフォントが見つかりません: {default_font_path}\n"
                "BIZ UDMinchoフォントがインストールされているか確認してください。"
            )
        config["fonts"] = {"main": str(default_font_path)}

    if "career_sheet_main" not in config["fonts"]:
        config["fonts"]["career_sheet_main"] = config["fonts"]["main"]

    return config
