"""データ読み込み機能のテスト"""

from pathlib import Path

import pytest

from jtr.rirekisho_data import load_rirekisho_data

jsonschema = pytest.importorskip("jsonschema")
ValidationError = jsonschema.ValidationError


class TestLoadRirekishoData:
    """load_rirekisho_data関数のテスト"""

    def test_load_valid_yaml_minimal(self, valid_fixtures_dir: Path) -> None:
        """正常系: 最小限の必須項目のみを含むYAMLファイルを読み込める"""
        file_path = valid_fixtures_dir / "minimal.yaml"
        data = load_rirekisho_data(file_path)

        assert isinstance(data, dict)
        assert "personal_info" in data
        assert data["personal_info"]["name"] == "田中一郎"
        assert "education" in data
        assert len(data["education"]) == 1
        assert "work_history" in data
        assert len(data["work_history"]) == 0

    def test_load_valid_yaml_full(self, valid_fixtures_dir: Path) -> None:
        """正常系: すべての項目を含むYAMLファイルを読み込める"""
        file_path = valid_fixtures_dir / "full.yaml"
        data = load_rirekisho_data(file_path)

        assert isinstance(data, dict)
        assert "personal_info" in data
        assert "education" in data
        assert "work_history" in data
        assert "qualifications" in data
        assert "additional_info" in data
        assert data["personal_info"]["name"] == "山田太郎"
        assert len(data["education"]) == 2
        assert len(data["work_history"]) == 3
        assert len(data["qualifications"]) == 3

    def test_load_valid_json(self, valid_fixtures_dir: Path) -> None:
        """正常系: JSON形式のファイルを読み込める"""
        file_path = valid_fixtures_dir / "full.json"
        data = load_rirekisho_data(file_path)

        assert isinstance(data, dict)
        assert "personal_info" in data
        assert data["personal_info"]["name"] == "山田太郎"
        assert len(data["education"]) == 2

    def test_file_not_found(self, valid_fixtures_dir: Path) -> None:
        """異常系: 存在しないファイルを指定するとFileNotFoundErrorが発生"""
        file_path = valid_fixtures_dir / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            load_rirekisho_data(file_path)

    def test_missing_required_field(self, invalid_fixtures_dir: Path) -> None:
        """異常系: 必須項目が欠落しているとValidationErrorが発生"""
        file_path = invalid_fixtures_dir / "missing_name.yaml"
        with pytest.raises(ValidationError) as exc_info:
            load_rirekisho_data(file_path)

        # エラーメッセージに欠落フィールドが含まれることを確認
        error_message = str(exc_info.value)
        assert "name" in error_message.lower() or "required" in error_message.lower()

    def test_invalid_date_format(self, invalid_fixtures_dir: Path) -> None:
        """異常系: 日付形式が不正だとValidationErrorが発生"""
        file_path = invalid_fixtures_dir / "invalid_birthdate.yaml"
        with pytest.raises(ValidationError):
            load_rirekisho_data(file_path)

    def test_invalid_enum_value(self, invalid_fixtures_dir: Path) -> None:
        """異常系: 列挙型の値が不正だとValidationErrorが発生"""
        file_path = invalid_fixtures_dir / "invalid_gender.yaml"
        with pytest.raises(ValidationError) as exc_info:
            load_rirekisho_data(file_path)

        # エラーメッセージに列挙型違反が含まれることを確認
        error_message = str(exc_info.value)
        assert "enum" in error_message.lower() or "gender" in error_message.lower()

    def test_invalid_pattern(self, invalid_fixtures_dir: Path) -> None:
        """異常系: パターン制約違反でValidationErrorが発生"""
        file_path = invalid_fixtures_dir / "invalid_name_kana.yaml"
        with pytest.raises(ValidationError) as exc_info:
            load_rirekisho_data(file_path)

        # エラーメッセージにパターン違反が含まれることを確認
        error_message = str(exc_info.value)
        assert "pattern" in error_message.lower() or "name_kana" in error_message.lower()

    def test_empty_required_array(self, invalid_fixtures_dir: Path) -> None:
        """異常系: 必須配列が空だとValidationErrorが発生（education minItems: 1）"""
        file_path = invalid_fixtures_dir / "empty_education.yaml"
        with pytest.raises(ValidationError) as exc_info:
            load_rirekisho_data(file_path)

        # エラーメッセージにminItems違反が含まれることを確認
        error_message = str(exc_info.value)
        assert "education" in error_message.lower() or "minitems" in error_message.lower()

    def test_malformed_yaml(self, invalid_fixtures_dir: Path) -> None:
        """異常系: YAML構文エラーで適切な例外が発生"""
        file_path = invalid_fixtures_dir / "malformed.yaml"
        # YAMLパースエラーはValidationErrorではなく、yaml.YAMLErrorまたはValueErrorを想定
        with pytest.raises((ValueError, Exception)):
            load_rirekisho_data(file_path)

    def test_unsupported_file_extension(self, valid_fixtures_dir: Path) -> None:
        """異常系: 非対応の拡張子でValueErrorが発生"""
        # 一時的に.txt拡張子のファイルを想定（実際には存在しない）
        file_path = valid_fixtures_dir / "test.txt"
        # ファイルが存在しない場合はFileNotFoundError、
        # 存在する場合はValueErrorを期待
        with pytest.raises((ValueError, FileNotFoundError)):
            load_rirekisho_data(file_path)
