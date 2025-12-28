"""履歴書データの読み込み・検証"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import jsonschema
import yaml


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


def load_resume_data(file_path: Path) -> dict[str, Any]:
    """
    YAML/JSONファイルから履歴書データを読み込み、スキーマ検証を行う

    Args:
        file_path: YAMLまたはJSONファイルのパス

    Returns:
        履歴書データ（schemas/resume_schema.json準拠）

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
    schema_path = Path(__file__).parent.parent.parent / "schemas" / "resume_schema.json"
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    jsonschema.validate(instance=data, schema=schema)

    # バリデーション成功後、dataはdict[str, Any]型として扱える
    return cast(dict[str, Any], data)
