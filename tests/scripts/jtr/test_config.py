"""skill.scripts.jtr.helper.config モジュールのテスト"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from jtr.helper.config import load_config, resolve_font_paths


class TestLoadConfig:
    """load_config関数のテスト"""

    def test_load_config_with_valid_file(self, tmp_path: Path) -> None:
        """有効なconfig.yamlを読み込める"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "options": {"date_format": "wareki", "paper_size": "B5"},
            "fonts": {
                "mincho": "fonts/custom_mincho.ttf",
                "gothic": "fonts/custom_gothic.ttf",
            },
            "styles": {
                "colors": {
                    "body_text": "#050315",
                    "main": "#6761af",
                    "sub": "#cdc69c",
                    "accent": "#e36162",
                }
            },
        }
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        result = load_config(config_file)

        assert result["options"]["date_format"] == "wareki"
        assert result["options"]["paper_size"] == "B5"
        assert result["fonts"]["mincho"] == "fonts/custom_mincho.ttf"
        assert result["fonts"]["gothic"] == "fonts/custom_gothic.ttf"
        assert result["styles"]["colors"]["body_text"] == "#050315"
        assert result["styles"]["colors"]["main"] == "#6761af"

    def test_load_config_with_nonexistent_file(self) -> None:
        """存在しないファイルを指定するとデフォルト設定が返る"""
        result = load_config(Path("/nonexistent/config.yaml"))

        assert result["options"]["date_format"] == "seireki"
        assert result["options"]["paper_size"] == "A4"
        assert result["fonts"] == {}

    def test_load_config_with_none(self) -> None:
        """Noneを指定するとデフォルト設定が返る"""
        result = load_config(None)

        assert result["options"]["date_format"] == "seireki"
        assert result["options"]["paper_size"] == "A4"
        assert result["fonts"] == {}

    def test_load_config_with_invalid_yaml(self, tmp_path: Path) -> None:
        """不正なYAMLを読み込むとValueErrorが発生"""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content:\n  - broken")

        with pytest.raises(ValueError, match="config.yamlの読み込みに失敗しました"):
            load_config(config_file)

    def test_load_config_with_non_dict_content(self, tmp_path: Path) -> None:
        """非辞書型のYAMLを読み込むとデフォルト設定が返る"""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("- item1\n- item2\n")

        result = load_config(config_file)

        assert result["options"] == {}
        assert result["fonts"] == {}


class TestResolveFontPaths:
    """resolve_font_paths関数のテスト"""

    def test_resolve_custom_mincho_font(self, tmp_path: Path) -> None:
        """カスタム明朝フォントの相対パスを絶対パスに解決"""
        # assets/ ディレクトリを作成
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        mincho_font = assets_dir / "mincho.ttf"
        mincho_font.touch()

        config = {"fonts": {"mincho": "mincho.ttf"}}

        with patch("jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = mincho_font
            result = resolve_font_paths(config)

        assert result["fonts"]["mincho"] == str(mincho_font)

    def test_resolve_nonexistent_mincho_font(self, tmp_path: Path) -> None:
        """存在しない明朝フォントを指定するとFileNotFoundErrorが発生"""
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        config = {"fonts": {"mincho": "nonexistent.ttf"}}

        with patch("jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = assets_dir / "nonexistent.ttf"
            with pytest.raises(FileNotFoundError, match="明朝フォントファイルが見つかりません"):
                resolve_font_paths(config)

    def test_resolve_default_font(self, tmp_path: Path) -> None:
        """カスタムフォントが指定されていない場合、デフォルトフォントを設定"""
        # デフォルトフォントのディレクトリ構造を作成（assets/fonts/）
        font_dir = tmp_path / "assets" / "fonts" / "BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        default_font = font_dir / "BIZUDMincho-Regular.ttf"
        default_font.touch()

        config: dict[str, str] = {}

        with patch("jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = default_font
            result = resolve_font_paths(config)

        assert result["fonts"]["mincho"] == str(default_font)

    def test_resolve_default_font_not_found(self, tmp_path: Path) -> None:
        """デフォルトフォントが存在しない場合、FileNotFoundErrorが発生"""
        font_dir = tmp_path / "assets" / "fonts" / "BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        config: dict[str, str] = {}

        with patch("jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = font_dir / "BIZUDMincho-Regular.ttf"  # 存在しない
            with pytest.raises(FileNotFoundError, match="デフォルトフォントが見つかりません"):
                resolve_font_paths(config)

    def test_resolve_empty_fonts_dict(self, tmp_path: Path) -> None:
        """空のfonts辞書の場合、デフォルトフォントを設定"""
        # デフォルトフォントのディレクトリ構造を作成（assets/fonts/）
        font_dir = tmp_path / "assets" / "fonts" / "BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        default_font = font_dir / "BIZUDMincho-Regular.ttf"
        default_font.touch()

        config = {"fonts": {}}

        with patch("jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = default_font
            result = resolve_font_paths(config)

        assert result["fonts"]["mincho"] == str(default_font)
