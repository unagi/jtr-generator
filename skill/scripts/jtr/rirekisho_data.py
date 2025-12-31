"""履歴書データの読み込み・検証"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import jsonschema
import yaml

from .helper.paths import get_schema_path


def _normalize_dates(data: Any) -> Any:
    """
    YAML読み込み時に自動変換されたdatetime.dateオブジェクトを文字列に変換

    Args:
        data: 任意のデータ構造

    Returns:
        日付オブジェクトが文字列に変換されたデータ
    """
    if isinstance(data, dict):
        return {key: _normalize_dates(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_normalize_dates(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, date):
        return data.isoformat()
    else:
        return data


def load_rirekisho_data(file_path: Path) -> dict[str, Any]:
    """
    YAML/JSONファイルから履歴書データを読み込み、スキーマ検証を行う

    Args:
        file_path: YAMLまたはJSONファイルのパス

    Returns:
        履歴書データ（schemas/rirekisho_schema.json準拠）

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: ファイル形式が非対応、またはYAML/JSONパースエラー
        jsonschema.ValidationError: スキーマバリデーション失敗時
    """
    # ファイル存在チェック
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 拡張子チェック
    suffix = file_path.suffix.lower()
    if suffix not in {".yaml", ".yml", ".json"}:
        raise ValueError(
            f"Unsupported file format: {suffix}. Only .yaml, .yml, or .json files are supported."
        )

    # ファイル読み込み
    try:
        with open(file_path, encoding="utf-8") as f:
            if suffix == ".json":
                data = json.load(f)
            else:  # .yaml or .yml
                data = yaml.safe_load(f)
                # YAMLの日付自動変換を元に戻す（JSON Schemaは文字列を期待）
                data = _normalize_dates(data)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML file: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON file: {e}") from e

    # スキーマバリデーション
    schema_path = get_schema_path("rirekisho_schema.json")
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.validate(instance=data, schema=schema)

    # バリデーション成功後、dataはdict[str, Any]型として扱える
    return cast(dict[str, Any], data)


def load_validated_data(
    file_path: str | Path,
    schema_name: str,
) -> dict[str, Any]:
    """
    YAML/JSONファイルから任意のデータを読み込み、指定されたスキーマで検証を行う

    Args:
        file_path: YAMLまたはJSONファイルのパス（またはYAML/JSON文字列）
        schema_name: スキーマファイル名（例: "rirekisho_schema.json"）

    Returns:
        検証済みデータ

    Raises:
        FileNotFoundError: ファイルやスキーマが存在しない場合
        ValueError: ファイル形式が非対応、またはYAML/JSONパースエラー
        jsonschema.ValidationError: スキーマバリデーション失敗時
    """
    # 文字列の場合はYAML/JSONとしてパース
    is_string_data = False
    if isinstance(file_path, str):
        # 改行を含む場合は確実に文字列データ
        if "\n" in file_path:
            is_string_data = True
        else:
            # 改行を含まない場合はファイルパスかもしれないので確認
            try:
                if not Path(file_path).exists():
                    is_string_data = True
            except OSError:
                # パスとして不正な場合（長すぎる等）は文字列データとして扱う
                is_string_data = True

    if is_string_data:
        # YAML/JSON文字列として解釈（型チェッカーのためにstr型として明示）
        input_str = str(file_path)
        try:
            data = yaml.safe_load(input_str)
            data = _normalize_dates(data)
        except yaml.YAMLError:
            # YAMLでパース失敗したらJSONとして試行
            try:
                data = json.loads(input_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse data string: {e}") from e
    else:
        # ファイルパスとして処理
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix not in {".yaml", ".yml", ".json"}:
            raise ValueError(
                f"Unsupported file format: {suffix}. Only .yaml, .yml, or .json files are supported."
            )

        with open(path, encoding="utf-8") as f:
            if suffix == ".json":
                data = json.load(f)
            else:  # .yaml or .yml
                data = yaml.safe_load(f)
                data = _normalize_dates(data)

    # スキーマバリデーション
    schema_path = get_schema_path(schema_name)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.validate(instance=data, schema=schema)

    return cast(dict[str, Any], data)


def format_validation_error_ja(error: jsonschema.ValidationError) -> str:
    """
    JSON Schemaバリデーションエラーを日本語で整形

    Args:
        error: jsonschema.ValidationError

    Returns:
        日本語エラーメッセージ
    """
    field_path = ".".join(str(p) for p in error.path) if error.path else "（ルート）"

    # よくあるエラーパターンを日本語化
    if error.validator == "required":  # type: ignore[comparison-overlap]
        missing_field = error.message.split("'")[1]
        return (
            f"必須フィールド '{missing_field}' が不足しています。\n"
            f"対象: {field_path}\n"
            f"assets/examples/sample_rirekisho.yamlを参考にデータを追加してください。"
        )
    elif error.validator == "pattern":  # type: ignore[comparison-overlap]
        expected_pattern = error.schema.get("pattern", "")  # type: ignore[union-attr]
        examples = error.schema.get("examples", [])  # type: ignore[union-attr]
        example_str = f"\n例: {examples[0]}" if examples else ""
        return (
            f"フィールド '{field_path}' の形式が不正です。\n"
            f"期待される形式: {expected_pattern}{example_str}"
        )
    elif error.validator == "enum":  # type: ignore[comparison-overlap]
        allowed_values = error.schema.get("enum", [])  # type: ignore[union-attr]
        return (
            f"フィールド '{field_path}' の値が不正です。\n"
            f"許可される値: {', '.join(str(v) for v in allowed_values)}"
        )
    elif error.validator == "format" and error.schema.get("format") == "date":  # type: ignore[comparison-overlap, union-attr]
        return (
            f"フィールド '{field_path}' の日付形式が不正です。\n"
            f"期待される形式: YYYY-MM-DD（例: 1990-04-01）"
        )
    elif error.validator == "minItems":  # type: ignore[comparison-overlap]
        min_items = error.schema.get("minItems", 0)  # type: ignore[union-attr]
        return (
            f"フィールド '{field_path}' は最低{min_items}件の要素が必要です。\n"
            f"現在の要素数: {len(error.instance) if isinstance(error.instance, list) else 0}"
        )
    else:
        return (
            f"データ検証エラー: {error.message}\n"
            f"対象フィールド: {field_path}\n"
            f"詳細: schemas/rirekisho_schema.jsonを参照してください。"
        )


def validate_and_load_data(input_data: str | Path) -> dict[str, Any]:
    """
    入力データをロード・バリデーション（エラーハンドリング強化版）

    Args:
        input_data: YAMLまたはJSON文字列、もしくはファイルパス

    Returns:
        バリデーション済み履歴書データ

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: データ形式エラー、パースエラー、バリデーションエラー
    """
    # ファイルパスの場合
    is_file_path = False
    if isinstance(input_data, Path):
        is_file_path = True
        file_path = input_data
    elif isinstance(input_data, str):
        # 改行を含む場合は文字列データとみなす（OSError回避）
        if "\n" not in input_data:
            try:
                file_path_candidate = Path(input_data)
                if file_path_candidate.exists():
                    is_file_path = True
                    file_path = file_path_candidate
            except OSError:
                # 長すぎるパス名などでエラーが発生した場合は文字列データとして扱う
                pass

    if is_file_path:
        try:
            return load_rirekisho_data(file_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}") from e
        except jsonschema.ValidationError as e:
            ja_message = format_validation_error_ja(e)
            raise ValueError(ja_message) from e
        except ValueError as e:
            raise ValueError(f"データの読み込みに失敗しました: {e}") from e

    # 文字列の場合（YAML/JSON）
    # input_dataはここまでに来た時点でstr型確定（Path型の場合は上のif is_file_pathで処理済み）
    input_str = str(input_data)  # 型チェッカーのために明示的に変換
    try:
        data = yaml.safe_load(input_str)
    except yaml.YAMLError:
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"YAML/JSONのパースに失敗しました: {e}") from e

    # スキーマバリデーション
    schema_path = get_schema_path("rirekisho_schema.json")
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        ja_message = format_validation_error_ja(e)
        raise ValueError(ja_message) from e

    # バリデーション済みなのでdict[str, Any]として返す
    return data  # type: ignore[no-any-return]
