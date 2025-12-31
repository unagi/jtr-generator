"""skill.scripts.jtr.helper.config モジュールのテスト"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from skill.scripts.jtr.helper.config import load_config, resolve_font_paths


class TestLoadConfig:
    """load_config関数のテスト"""

    def test_load_config_with_valid_file(self, tmp_path: Path) -> None:
        """有効なconfig.yamlを読み込める"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "options": {"date_format": "wareki", "paper_size": "B5"},
            "fonts": {
                "main": "fonts/custom.ttf",
                "career_sheet_main": "fonts/gothic.ttf",
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
        assert result["fonts"]["main"] == "fonts/custom.ttf"
        assert result["fonts"]["career_sheet_main"] == "fonts/gothic.ttf"
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

    def test_resolve_custom_main_font(self, tmp_path: Path) -> None:
        """カスタムメインフォントの相対パスを絶対パスに解決"""
        # assets/ ディレクトリを作成
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        font_file = assets_dir / "custom.ttf"
        font_file.touch()

        config = {"fonts": {"main": "custom.ttf"}}

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = font_file
            result = resolve_font_paths(config)

        assert result["fonts"]["main"] == str(font_file)

    def test_resolve_custom_heading_font(self, tmp_path: Path) -> None:
        """カスタム見出しフォントの相対パスを絶対パスに解決"""
        # assets/ ディレクトリを作成
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        main_font = assets_dir / "main.ttf"
        heading_font = assets_dir / "heading.ttf"
        main_font.touch()
        heading_font.touch()

        config = {"fonts": {"main": "main.ttf", "heading": "heading.ttf"}}

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.side_effect = lambda x: assets_dir / x
            result = resolve_font_paths(config)

        assert result["fonts"]["main"] == str(main_font)
        assert result["fonts"]["heading"] == str(heading_font)

    def test_resolve_career_sheet_font(self, tmp_path: Path) -> None:
        """職務経歴書フォントの相対パスを絶対パスに解決"""
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        main_font = assets_dir / "main.ttf"
        career_font = assets_dir / "career.ttf"
        main_font.touch()
        career_font.touch()

        config = {"fonts": {"main": "main.ttf", "career_sheet_main": "career.ttf"}}

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.side_effect = lambda x: assets_dir / x
            result = resolve_font_paths(config)

        assert result["fonts"]["main"] == str(main_font)
        assert result["fonts"]["career_sheet_main"] == str(career_font)

    def test_resolve_nonexistent_main_font(self, tmp_path: Path) -> None:
        """存在しないメインフォントを指定するとFileNotFoundErrorが発生"""
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        config = {"fonts": {"main": "nonexistent.ttf"}}

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = assets_dir / "nonexistent.ttf"
            with pytest.raises(FileNotFoundError, match="カスタムフォントファイルが見つかりません"):
                resolve_font_paths(config)

    def test_resolve_nonexistent_heading_font(self, tmp_path: Path) -> None:
        """存在しない見出しフォントを指定するとFileNotFoundErrorが発生"""
        # assets/ ディレクトリを作成
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        main_font = assets_dir / "main.ttf"
        main_font.touch()

        config = {"fonts": {"main": "main.ttf", "heading": "nonexistent.ttf"}}

        def mock_side_effect(x):
            if x == "main.ttf":
                return main_font
            return assets_dir / "nonexistent.ttf"

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.side_effect = mock_side_effect
            with pytest.raises(FileNotFoundError, match="見出しフォントファイルが見つかりません"):
                resolve_font_paths(config)

    def test_resolve_default_font(self, tmp_path: Path) -> None:
        """カスタムフォントが指定されていない場合、デフォルトフォントを設定"""
        # デフォルトフォントのディレクトリ構造を作成（assets/fonts/）
        font_dir = tmp_path / "assets" / "fonts" / "BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        default_font = font_dir / "BIZUDMincho-Regular.ttf"
        default_font.touch()

        config: dict[str, str] = {}

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = default_font
            result = resolve_font_paths(config)

        assert result["fonts"]["main"] == str(default_font)

    def test_resolve_default_font_not_found(self, tmp_path: Path) -> None:
        """デフォルトフォントが存在しない場合、FileNotFoundErrorが発生"""
        font_dir = tmp_path / "assets" / "fonts" / "BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        config: dict[str, str] = {}

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
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

        with patch("skill.scripts.jtr.helper.config.get_assets_path") as mock_get_assets:
            mock_get_assets.return_value = default_font
            result = resolve_font_paths(config)

        assert result["fonts"]["main"] == str(default_font)
