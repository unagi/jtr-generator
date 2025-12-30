"""skill.jtr.config モジュールのテスト"""

from pathlib import Path

import pytest
import yaml

from skill.jtr.config import load_config, resolve_font_paths


class TestLoadConfig:
    """load_config関数のテスト"""

    def test_load_config_with_valid_file(self, tmp_path: Path) -> None:
        """有効なconfig.yamlを読み込める"""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "options": {"date_format": "wareki", "paper_size": "B5"},
            "fonts": {"main": "fonts/custom.ttf"},
        }
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        result = load_config(config_file)

        assert result["options"]["date_format"] == "wareki"
        assert result["options"]["paper_size"] == "B5"
        assert result["fonts"]["main"] == "fonts/custom.ttf"

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
        font_file = tmp_path / "custom.ttf"
        font_file.touch()

        config = {"fonts": {"main": "custom.ttf"}}
        result = resolve_font_paths(config, tmp_path)

        assert result["fonts"]["main"] == str(font_file)

    def test_resolve_custom_heading_font(self, tmp_path: Path) -> None:
        """カスタム見出しフォントの相対パスを絶対パスに解決"""
        main_font = tmp_path / "main.ttf"
        heading_font = tmp_path / "heading.ttf"
        main_font.touch()
        heading_font.touch()

        config = {"fonts": {"main": "main.ttf", "heading": "heading.ttf"}}
        result = resolve_font_paths(config, tmp_path)

        assert result["fonts"]["main"] == str(main_font)
        assert result["fonts"]["heading"] == str(heading_font)

    def test_resolve_nonexistent_main_font(self, tmp_path: Path) -> None:
        """存在しないメインフォントを指定するとFileNotFoundErrorが発生"""
        config = {"fonts": {"main": "nonexistent.ttf"}}

        with pytest.raises(
            FileNotFoundError, match="カスタムフォントファイルが見つかりません"
        ):
            resolve_font_paths(config, tmp_path)

    def test_resolve_nonexistent_heading_font(self, tmp_path: Path) -> None:
        """存在しない見出しフォントを指定するとFileNotFoundErrorが発生"""
        main_font = tmp_path / "main.ttf"
        main_font.touch()

        config = {"fonts": {"main": "main.ttf", "heading": "nonexistent.ttf"}}

        with pytest.raises(
            FileNotFoundError, match="見出しフォントファイルが見つかりません"
        ):
            resolve_font_paths(config, tmp_path)

    def test_resolve_default_font(self, tmp_path: Path) -> None:
        """カスタムフォントが指定されていない場合、デフォルトフォントを設定"""
        # デフォルトフォントのディレクトリ構造を作成
        font_dir = tmp_path / "fonts/BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        default_font = font_dir / "BIZUDMincho-Regular.ttf"
        default_font.touch()

        config: dict[str, str] = {}
        result = resolve_font_paths(config, tmp_path)

        assert result["fonts"]["main"] == str(default_font)

    def test_resolve_default_font_not_found(self, tmp_path: Path) -> None:
        """デフォルトフォントが存在しない場合、FileNotFoundErrorが発生"""
        config: dict[str, str] = {}

        with pytest.raises(FileNotFoundError, match="デフォルトフォントが見つかりません"):
            resolve_font_paths(config, tmp_path)

    def test_resolve_empty_fonts_dict(self, tmp_path: Path) -> None:
        """空のfonts辞書の場合、デフォルトフォントを設定"""
        font_dir = tmp_path / "fonts/BIZ_UDMincho"
        font_dir.mkdir(parents=True)
        default_font = font_dir / "BIZUDMincho-Regular.ttf"
        default_font.touch()

        config = {"fonts": {}}
        result = resolve_font_paths(config, tmp_path)

        assert result["fonts"]["main"] == str(default_font)
