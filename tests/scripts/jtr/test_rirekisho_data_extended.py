"""skill.scripts.jtr.rirekisho_data モジュールの拡張機能テスト（format_validation_error_ja, validate_and_load_data, load_validated_data）"""

import json
from pathlib import Path

import jsonschema
import pytest

from jtr.rirekisho_data import (
    format_validation_error_ja,
    load_validated_data,
    validate_and_load_data,
)


class TestFormatValidationErrorJa:
    """format_validation_error_ja関数のテスト"""

    def test_format_required_error(self) -> None:
        """必須フィールド不足エラーを日本語で整形"""
        schema = {"type": "object", "required": ["name"]}
        data = {}

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            result = format_validation_error_ja(e)

            assert "必須フィールド 'name' が不足しています" in result
            assert "assets/examples/sample_rirekisho.yaml" in result

    def test_format_pattern_error(self) -> None:
        """パターン制約違反エラーを日本語で整形"""
        schema = {
            "type": "object",
            "properties": {
                "postal_code": {
                    "type": "string",
                    "pattern": "^\\d{3}-\\d{4}$",
                    "examples": ["123-4567"],
                }
            },
        }
        data = {"postal_code": "invalid"}

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            result = format_validation_error_ja(e)

            assert "形式が不正です" in result
            assert "123-4567" in result

    def test_format_enum_error(self) -> None:
        """列挙型違反エラーを日本語で整形"""
        schema = {
            "type": "object",
            "properties": {"gender": {"type": "string", "enum": ["男性", "女性", "その他"]}},
        }
        data = {"gender": "invalid"}

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            result = format_validation_error_ja(e)

            assert "値が不正です" in result
            assert "男性" in result
            assert "女性" in result

    def test_format_date_format_error(self) -> None:
        """日付形式エラーを日本語で整形"""
        schema = {
            "type": "object",
            "properties": {"birthdate": {"type": "string", "format": "date"}},
        }
        data = {"birthdate": "invalid-date"}

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            result = format_validation_error_ja(e)

            assert "日付形式が不正です" in result
            assert "YYYY-MM-DD" in result

    def test_format_min_items_error(self) -> None:
        """配列最小要素数違反エラーを日本語で整形"""
        schema = {
            "type": "object",
            "properties": {"education": {"type": "array", "minItems": 1}},
        }
        data = {"education": []}

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            result = format_validation_error_ja(e)

            assert "最低1件の要素が必要です" in result
            assert "現在の要素数: 0" in result

    def test_format_generic_error(self) -> None:
        """その他のエラーを汎用フォーマットで整形"""
        schema = {"type": "string"}
        data = 123

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            result = format_validation_error_ja(e)

            assert "データ検証エラー" in result
            assert "schemas/rirekisho_schema.json" in result


class TestValidateAndLoadData:
    """validate_and_load_data関数のテスト"""

    @pytest.fixture
    def sample_data_dict(self) -> dict:
        """サンプル履歴書データ"""
        return {
            "personal_info": {
                "name": "山田太郎",
                "name_kana": "やまだたろう",
                "birthdate": "1990-04-01",
                "gender": "男性",
                "postal_code": "150-0041",
                "address": "東京都渋谷区神南1-1-1",
                "phone": "03-1234-5678",
                "email": "yamada@example.com",
            },
            "education": [
                {
                    "date": "2009-04",
                    "school": "○○大学",
                    "type": "入学",
                }
            ],
            "work_history": [],  # 必須フィールド
        }

    def test_load_from_valid_yaml_file(self, tmp_path: Path, sample_data_dict: dict) -> None:
        """有効なYAMLファイルを読み込める"""
        yaml_file = tmp_path / "rirekisho.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            import yaml

            yaml.dump(sample_data_dict, f, allow_unicode=True)

        result = validate_and_load_data(yaml_file)

        assert result["personal_info"]["name"] == "山田太郎"
        assert result["education"][0]["school"] == "○○大学"

    def test_load_from_valid_json_file(self, tmp_path: Path, sample_data_dict: dict) -> None:
        """有効なJSONファイルを読み込める"""
        json_file = tmp_path / "rirekisho.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(sample_data_dict, f, ensure_ascii=False)

        result = validate_and_load_data(json_file)

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_from_valid_yaml_string(self, sample_data_dict: dict) -> None:
        """有効なYAML文字列を読み込める"""
        import yaml

        yaml_str = yaml.dump(sample_data_dict, allow_unicode=True)

        result = validate_and_load_data(yaml_str)

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_from_valid_json_string(self, sample_data_dict: dict) -> None:
        """有効なJSON文字列を読み込める"""
        json_str = json.dumps(sample_data_dict, ensure_ascii=False)

        result = validate_and_load_data(json_str)

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_nonexistent_file(self) -> None:
        """存在しないファイルを指定するとFileNotFoundErrorが発生"""
        with pytest.raises(FileNotFoundError, match="ファイルが見つかりません"):
            validate_and_load_data(Path("/nonexistent/rirekisho.yaml"))

    def test_load_invalid_yaml_string(self) -> None:
        """不正なYAML/JSON文字列を読み込むとValueErrorが発生"""
        invalid_str = "invalid: yaml: content:\n  - broken"

        with pytest.raises(ValueError, match="YAML/JSONのパースに失敗しました"):
            validate_and_load_data(invalid_str)

    def test_load_string_with_validation_error(self) -> None:
        """バリデーションエラーがある文字列を読み込むとValueErrorが発生"""
        import yaml

        invalid_data = {"personal_info": {}}  # 必須フィールドが不足
        yaml_str = yaml.dump(invalid_data)

        with pytest.raises(ValueError, match="必須フィールド"):
            validate_and_load_data(yaml_str)

    def test_load_file_with_validation_error(self, tmp_path: Path) -> None:
        """バリデーションエラーがあるファイルを読み込むとValueErrorが発生"""
        invalid_data = {"personal_info": {}}  # 必須フィールドが不足
        yaml_file = tmp_path / "invalid.yaml"

        import yaml

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_data, f)

        with pytest.raises(ValueError, match="必須フィールド"):
            validate_and_load_data(yaml_file)

    def test_load_file_with_parse_error(self, tmp_path: Path) -> None:
        """パースエラーがあるファイルを読み込むとValueErrorが発生"""
        yaml_file = tmp_path / "broken.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content:\n  - broken")

        with pytest.raises(ValueError, match="データの読み込みに失敗しました"):
            validate_and_load_data(yaml_file)

    def test_load_json_string_fallback_after_yaml_parse_failure(
        self, sample_data_dict: dict
    ) -> None:
        """YAML解析失敗後にJSON文字列としてfallbackする"""
        # YAMLとして不正だがJSONとして有効な文字列
        json_str = json.dumps(sample_data_dict, ensure_ascii=False)

        result = validate_and_load_data(json_str)

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_from_json_file_directly(self, tmp_path: Path, sample_data_dict: dict) -> None:
        """JSONファイルを直接読み込む（line 131-132をカバー）"""
        json_file = tmp_path / "rirekisho.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(sample_data_dict, f, ensure_ascii=False)

        result = validate_and_load_data(json_file)

        assert result["personal_info"]["name"] == "山田太郎"
        assert len(result["education"]) == 1


class TestLoadValidatedData:
    """load_validated_data関数のテスト（汎用スキーマ対応版）"""

    @pytest.fixture
    def sample_data_dict(self) -> dict:
        """サンプル履歴書データ"""
        return {
            "personal_info": {
                "name": "山田太郎",
                "name_kana": "やまだたろう",
                "birthdate": "1990-04-01",
                "gender": "男性",
                "postal_code": "150-0041",
                "address": "東京都渋谷区神南1-1-1",
                "phone": "03-1234-5678",
                "email": "yamada@example.com",
            },
            "education": [
                {
                    "date": "2009-04",
                    "school": "○○大学",
                    "type": "入学",
                }
            ],
            "work_history": [],
        }

    def test_load_yaml_string_with_schema(self, sample_data_dict: dict) -> None:
        """YAML文字列を指定スキーマで読み込む（line 107-111カバー）"""
        import yaml

        yaml_str = yaml.dump(sample_data_dict, allow_unicode=True)

        result = load_validated_data(yaml_str, "rirekisho_schema.json")

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_json_string_with_schema(self, sample_data_dict: dict) -> None:
        """JSON文字列を指定スキーマで読み込む（line 114-117カバー）"""
        json_str = json.dumps(sample_data_dict, ensure_ascii=False)

        result = load_validated_data(json_str, "rirekisho_schema.json")

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_json_file_with_schema(self, tmp_path: Path, sample_data_dict: dict) -> None:
        """JSONファイルを指定スキーマで読み込む（line 131-132カバー）"""
        json_file = tmp_path / "rirekisho.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(sample_data_dict, f, ensure_ascii=False)

        result = load_validated_data(json_file, "rirekisho_schema.json")

        assert result["personal_info"]["name"] == "山田太郎"

    def test_load_yaml_file_with_schema(self, tmp_path: Path, sample_data_dict: dict) -> None:
        """YAMLファイルを指定スキーマで読み込む（line 134-135カバー）"""
        import yaml

        yaml_file = tmp_path / "rirekisho.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_data_dict, f, allow_unicode=True)

        result = load_validated_data(yaml_file, "rirekisho_schema.json")

        assert result["personal_info"]["name"] == "山田太郎"
