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
from typing import Any

from jtr import (
    generate_resume_pdf,
    load_config,
    resolve_font_paths,
    validate_and_load_data,
)


def main(
    input_data: str | Path,
    session_options: dict[str, Any] | None = None,
    output_path: Path | str | None = None,
) -> Path:
    """
    Claude Agent Skills環境から呼び出されるメイン関数

    Args:
        input_data: ユーザーが提供したYAML/JSONデータ（文字列またはファイルパス）
        session_options: セッション固有のオプション（和暦/西暦、用紙サイズ等）
        output_path: 出力PDFファイルのパス（Noneの場合はカレントディレクトリに rirekisho.pdf を生成）

    Returns:
        生成されたPDFファイルのパス

    Raises:
        FileNotFoundError: ファイルやフォントが存在しない場合
        ValueError: データ形式エラー、バリデーションエラー
    """
    # 1. 設定読み込み（config.yaml）
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path if config_path.exists() else None)

    # 2. フォントパス解決
    base_dir = Path(__file__).parent
    config = resolve_font_paths(config, base_dir)

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

    # 出力パスの決定
    if output_path is None:
        final_output_path = Path("rirekisho.pdf")
    else:
        final_output_path = Path(output_path)

    generate_resume_pdf(data, options, final_output_path)

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
