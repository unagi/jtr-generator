"""日本の履歴書生成 - Claude Agent Skills エントリーポイント"""

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

# 共通実装をインポート
from jtr import generate_resume_pdf, load_resume_data


def load_claude_config() -> dict[str, Any]:
    """
    Claude Agent Skills環境からconfig.yamlを読み込み

    Returns:
        設定辞書（date_format, paper_size, fonts等）

    Raises:
        ValueError: config.yamlのパースエラー時
    """
    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
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
    base_dir = Path(__file__).parent  # skill/

    # カスタムフォントが指定されている場合
    if "fonts" in config and config["fonts"]:
        if "main" in config["fonts"]:
            custom_font_path = base_dir / config["fonts"]["main"]
            if not custom_font_path.exists():
                raise FileNotFoundError(
                    f"カスタムフォントファイルが見つかりません: {custom_font_path}\n"
                    "config.yamlのfonts.main設定を確認してください。"
                )
            config["fonts"]["main"] = str(custom_font_path)

        if "heading" in config["fonts"]:
            heading_font_path = base_dir / config["fonts"]["heading"]
            if not heading_font_path.exists():
                raise FileNotFoundError(
                    f"見出しフォントファイルが見つかりません: {heading_font_path}\n"
                    "config.yamlのfonts.heading設定を確認してください。"
                )
            config["fonts"]["heading"] = str(heading_font_path)
    else:
        # デフォルトフォントを設定
        default_font_path = base_dir / "fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf"
        if not default_font_path.exists():
            raise FileNotFoundError(
                f"デフォルトフォントが見つかりません: {default_font_path}\n"
                "BIZ UDMinchoフォントがインストールされているか確認してください。"
            )
        config["fonts"] = {"main": str(default_font_path)}

    return config


def _format_validation_error_ja(error: jsonschema.ValidationError) -> str:
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
            f"examples/sample_resume.yamlを参考にデータを追加してください。"
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
            f"詳細: schemas/resume_schema.jsonを参照してください。"
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
    if isinstance(input_data, Path) or (isinstance(input_data, str) and Path(input_data).exists()):
        file_path = Path(input_data)
        try:
            return load_resume_data(file_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}") from e
        except jsonschema.ValidationError as e:
            ja_message = _format_validation_error_ja(e)
            raise ValueError(ja_message) from e
        except ValueError as e:
            raise ValueError(f"データの読み込みに失敗しました: {e}") from e

    # 文字列の場合（YAML/JSON）
    try:
        data = yaml.safe_load(input_data)
    except yaml.YAMLError:
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"YAML/JSONのパースに失敗しました: {e}") from e

    # スキーマバリデーション
    schema_path = Path(__file__).resolve().parent / "schemas" / "resume_schema.json"
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        ja_message = _format_validation_error_ja(e)
        raise ValueError(ja_message) from e

    # バリデーション済みなのでdict[str, Any]として返す
    return data  # type: ignore[no-any-return]


def main(input_data: str | Path, session_options: dict[str, Any] | None = None) -> Path:
    """
    Claude Agent Skills環境から呼び出されるメイン関数

    Args:
        input_data: ユーザーが提供したYAML/JSONデータ（文字列またはファイルパス）
        session_options: セッション固有のオプション（和暦/西暦、用紙サイズ等）

    Returns:
        生成されたPDFファイルのパス

    Raises:
        FileNotFoundError: ファイルやフォントが存在しない場合
        ValueError: データ形式エラー、バリデーションエラー
    """
    # 1. 設定読み込み（config.yaml）
    config = load_claude_config()

    # 2. フォントパス解決
    config = resolve_font_paths(config)

    # 3. セッションオプションで上書き（例: 「和暦で表記してください」）
    if session_options:
        if "date_format" in session_options:
            config["options"]["date_format"] = session_options["date_format"]
        if "paper_size" in session_options:
            config["options"]["paper_size"] = session_options["paper_size"]

    # 4. データ読み込み・バリデーション
    data = validate_and_load_data(input_data)

    # 5. PDF生成（フォント設定を含める）
    options = dict(config.get("options", {}))
    options["fonts"] = config.get("fonts", {})
    output_path = Path("/tmp/rirekisho.pdf")
    generate_resume_pdf(data, options, output_path)

    return output_path


if __name__ == "__main__":
    # ローカルテスト用のエントリーポイント
    import argparse

    parser = argparse.ArgumentParser(description="日本の履歴書PDF生成")
    parser.add_argument("input_file", type=Path, help="入力YAMLまたはJSONファイル")
    parser.add_argument(
        "--date-format", choices=["seireki", "wareki"], default="seireki", help="日付形式"
    )
    parser.add_argument("--paper-size", choices=["A4", "B5"], default="A4", help="用紙サイズ")
    args = parser.parse_args()

    session_options = {"date_format": args.date_format, "paper_size": args.paper_size}

    try:
        output = main(args.input_file, session_options)
        print(f"履歴書PDFを生成しました: {output}")
    except (FileNotFoundError, ValueError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
