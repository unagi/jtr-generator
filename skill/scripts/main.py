"""日本の履歴書生成 - Claude Agent Skills エントリーポイント

このモジュールはClaudeSkillsのエントリーポイントとして機能し、
共通実装（jtrパッケージ）への薄いラッパーを提供します。

Progressive Disclosure:

Overview:
JIS規格準拠の日本の履歴書をPDF形式で生成します。
対話的な情報収集またはYAML/JSONファイルからの生成が可能です。

Details:
- 入力形式: チャットテキスト、YAML、JSON
- 出力形式: PDF（A4のみ、和暦/西暦切り替え可能）
- カスタムフォント対応
- JSON Schema準拠のバリデーション

Examples:
1. 対話的生成:
   「履歴書を作成してください。氏名は山田太郎です。」

2. ファイルからの生成:
   [YAMLファイルを添付] 「このファイルから履歴書を生成してください。」

3. オプション指定:
   「A4サイズ、和暦で履歴書を作成してください。」
"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .jtr import (
        generate_career_sheet_pdf,
        generate_resume_pdf,
        load_config,
        load_validated_data,
        resolve_font_paths,
        validate_and_load_data,
    )
    from .jtr.paths import get_assets_path
elif __package__:
    from .jtr import (
        generate_career_sheet_pdf,
        generate_resume_pdf,
        load_config,
        load_validated_data,
        resolve_font_paths,
        validate_and_load_data,
    )
    from .jtr.paths import get_assets_path
else:
    from jtr import (
        generate_career_sheet_pdf,
        generate_resume_pdf,
        load_config,
        load_validated_data,
        resolve_font_paths,
        validate_and_load_data,
    )
    from jtr.paths import get_assets_path


def main(
    input_data: str | Path,
    session_options: dict[str, Any] | None = None,
    output_path: Path | str | None = None,
    document_type: str = "resume",
    markdown_content: str | Path | None = None,
    additional_info: str | Path | None = None,
) -> Path:
    """
    Claude Agent Skills環境から呼び出されるメイン関数

    Args:
        input_data: ユーザーが提供したYAML/JSONデータ（文字列またはファイルパス）
        session_options: セッション固有のオプション（和暦/西暦、用紙サイズ等）
        output_path: 出力PDFファイルのパス（Noneの場合は document_type に応じたデフォルト名）
        document_type: ドキュメントタイプ（"resume" または "career_sheet"）
        markdown_content: 職務経歴書本文（Markdown形式、文字列またはファイルパス）
        additional_info: 追加情報（YAML/JSON形式、文字列またはファイルパス）

    Returns:
        生成されたPDFファイルのパス

    Raises:
        FileNotFoundError: ファイルやフォントが存在しない場合
        ValueError: データ形式エラー、バリデーションエラー
    """
    # 1. 設定読み込み（config.yaml）
    config_path = get_assets_path("config.yaml")
    config = load_config(config_path if config_path.exists() else None)

    # 2. フォントパス解決
    config = resolve_font_paths(config)

    # 3. セッションオプションで上書き（例: 「和暦で表記してください」）
    if session_options:
        if "date_format" in session_options:
            config["options"]["date_format"] = session_options["date_format"]
        if "paper_size" in session_options:
            config["options"]["paper_size"] = session_options["paper_size"]

    # 4. PDF生成オプション
    options = dict(config.get("options", {}))
    options["fonts"] = config.get("fonts", {})

    # 5. document_typeで分岐
    if document_type == "resume":
        # 履歴書生成
        data = validate_and_load_data(input_data)
        final_output_path = Path(output_path) if output_path else Path("rirekisho.pdf")
        generate_resume_pdf(data, options, final_output_path)

    elif document_type == "career_sheet":
        # 職務経歴書生成
        if markdown_content is None:
            raise ValueError("職務経歴書生成には markdown_content が必要です")
        if additional_info is None:
            raise ValueError("職務経歴書生成には additional_info が必要です")

        # 履歴書データの読み込み（resume_schema.jsonでバリデーション）
        resume_data = load_validated_data(input_data, "resume_schema.json")

        # Markdownコンテンツの読み込み
        if isinstance(markdown_content, (str, Path)):
            markdown_path = Path(markdown_content)
            if markdown_path.exists():
                markdown_text = markdown_path.read_text(encoding="utf-8")
            else:
                # ファイルが存在しない場合は、文字列として扱う
                markdown_text = str(markdown_content)
        else:
            markdown_text = markdown_content

        # 追加情報の読み込み（additional_info_schema.jsonでバリデーション）
        additional_data = load_validated_data(additional_info, "additional_info_schema.json")

        # 出力パス決定
        final_output_path = Path(output_path) if output_path else Path("career_sheet.pdf")

        # PDF生成
        generate_career_sheet_pdf(
            resume_data, markdown_text, additional_data, options, final_output_path
        )

    else:
        raise ValueError(f"不明な document_type: {document_type}")

    return final_output_path


if __name__ == "__main__":
    # ローカルテスト用のエントリーポイント
    import argparse

    parser = argparse.ArgumentParser(description="日本の履歴書PDF生成")
    parser.add_argument("input_file", type=Path, help="入力YAMLまたはJSONファイル")
    parser.add_argument(
        "--date-format", choices=["seireki", "wareki"], default="seireki", help="日付形式"
    )
    parser.add_argument(
        "--paper-size", choices=["A4", "B5"], default="A4", help="用紙サイズ（B5は将来対応予定）"
    )
    args = parser.parse_args()

    session_options = {"date_format": args.date_format, "paper_size": args.paper_size}

    try:
        output = main(args.input_file, session_options)
        print(f"履歴書PDFを生成しました: {output}")
    except (FileNotFoundError, ValueError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
