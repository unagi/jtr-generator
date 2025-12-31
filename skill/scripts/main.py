"""日本のレジュメ（履歴書・職務経歴書）生成 - Claude Agent Skills エントリーポイント

このモジュールはClaudeSkillsのエントリーポイントとして機能し、
共通実装（jtrパッケージ）への薄いラッパーを提供します。

Progressive Disclosure:

Overview:
JIS規格準拠の日本のレジュメをPDF形式で生成します。
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
# ruff: isort: skip_file

import sys
from datetime import UTC, datetime
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from jtr import (  # noqa: E402
    generate_career_sheet_pdf,
    generate_rirekisho_pdf,
    load_config,
    resolve_font_paths,
    validate_and_load_data,
)
from jtr.helper.paths import get_assets_path  # noqa: E402


def _add_common_options(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--date-format",
        choices=["seireki", "wareki"],
        default="seireki",
        help="日付形式",
    )
    parser.add_argument(
        "--paper-size",
        choices=["A4", "B5"],
        default="A4",
        help="用紙サイズ（B5は将来対応予定）",
    )
    parser.add_argument(
        "--font",
        choices=["mincho", "gothic"],
        default=None,
        help="明朝/ゴシックの選択（両ドキュメント共通）",
    )


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="日本のレジュメ（履歴書・職務経歴書）PDF生成")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rirekisho_parser = subparsers.add_parser("rirekisho", help="履歴書PDFを生成")
    rirekisho_parser.add_argument("input_file", type=Path, help="入力YAMLまたはJSONファイル")
    rirekisho_parser.add_argument("--output", type=Path, default=None, help="出力PDFファイル")
    _add_common_options(rirekisho_parser)

    career_parser = subparsers.add_parser("career_sheet", help="職務経歴書PDFを生成")
    career_parser.add_argument("input_file", type=Path, help="入力YAMLまたはJSONファイル")
    career_parser.add_argument("markdown_file", type=Path, help="Markdown本文ファイル")
    career_parser.add_argument("--output", type=Path, default=None, help="出力PDFファイル")
    _add_common_options(career_parser)

    both_parser = subparsers.add_parser("both", help="履歴書と職務経歴書をまとめて生成")
    both_parser.add_argument("input_file", type=Path, help="入力YAMLまたはJSONファイル")
    both_parser.add_argument("markdown_file", type=Path, help="Markdown本文ファイル")
    both_parser.add_argument("--output-dir", type=Path, default=None, help="出力先ディレクトリ")
    _add_common_options(both_parser)

    return parser.parse_args()


def _build_options(session_options: dict[str, Any] | None) -> dict[str, Any]:
    config_path = get_assets_path("config.yaml")
    config = load_config(config_path if config_path.exists() else None)
    config = resolve_font_paths(config)

    if session_options:
        config_options = config.setdefault("options", {})
        for key in ("date_format", "paper_size"):
            if key in session_options:
                config_options[key] = session_options[key]
        if "font" in session_options and session_options["font"]:
            config_options["font"] = session_options["font"]

    options = dict(config.get("options", {}))
    options["fonts"] = config.get("fonts", {})
    options["styles"] = config.get("styles", {})
    return options


def _load_markdown(markdown_content: str | Path | None) -> str:
    if markdown_content is None:
        raise ValueError("職務経歴書生成には markdown_content が必要です")

    if isinstance(markdown_content, (str, Path)):
        markdown_path = Path(markdown_content)
        if markdown_path.exists():
            return markdown_path.read_text(encoding="utf-8")
        return str(markdown_content)

    return str(markdown_content)


def _build_both_output_paths(output_dir: Path) -> tuple[Path, Path]:
    timestamp = datetime.now(UTC).strftime("%y%m%d-%H%M%S")
    return (
        output_dir / f"rirekisho_{timestamp}.pdf",
        output_dir / f"career_sheet_{timestamp}.pdf",
    )


def main(
    input_data: str | Path,
    session_options: dict[str, Any] | None = None,
    output_path: Path | str | None = None,
    document_type: str = "rirekisho",
    markdown_content: str | Path | None = None,
) -> Path | list[Path]:
    """
    Claude Agent Skills環境から呼び出されるメイン関数

    Args:
        input_data: ユーザーが提供したYAML/JSONデータ（文字列またはファイルパス）
        session_options: セッション固有のオプション（和暦/西暦、用紙サイズ等）
        output_path: 出力PDFファイルのパス（bothの場合は出力ディレクトリ）
        document_type: ドキュメントタイプ（"rirekisho", "career_sheet", "both"）
        markdown_content: 職務経歴書本文（Markdown形式、文字列またはファイルパス）

    Returns:
        生成されたPDFファイルのパス（bothの場合は2件のリスト）

    Raises:
        FileNotFoundError: ファイルやフォントが存在しない場合
        ValueError: データ形式エラー、バリデーションエラー
    """
    options = _build_options(session_options)

    make_rirekisho = document_type in ("rirekisho", "both")
    make_career = document_type in ("career_sheet", "both")

    if not make_rirekisho and not make_career:
        raise ValueError(f"不明な document_type: {document_type}")

    rirekisho_data = validate_and_load_data(input_data)
    markdown_text = _load_markdown(markdown_content) if make_career else None

    outputs: list[Path] = []
    output_dir: Path | None = None

    if document_type == "both":
        output_dir = Path(output_path) if output_path else Path(".")
        if output_dir.suffix:
            raise ValueError("bothの出力先はディレクトリを指定してください")
        if output_dir.exists() and not output_dir.is_dir():
            raise ValueError("bothの出力先はディレクトリを指定してください")
        output_dir.mkdir(parents=True, exist_ok=True)

    if output_dir:
        rirekisho_output_path, career_output_path = _build_both_output_paths(output_dir)

    if make_rirekisho:
        if not output_dir:
            rirekisho_output_path = Path(output_path) if output_path else Path("rirekisho.pdf")
        generate_rirekisho_pdf(rirekisho_data, options, rirekisho_output_path)
        outputs.append(rirekisho_output_path)

    if make_career:
        if markdown_text is None:
            raise ValueError("職務経歴書生成には markdown_content が必要です")
        if not output_dir:
            career_output_path = Path(output_path) if output_path else Path("career_sheet.pdf")
        generate_career_sheet_pdf(rirekisho_data, markdown_text, options, career_output_path)
        outputs.append(career_output_path)

    if document_type == "both":
        return outputs
    return outputs[0]


if __name__ == "__main__":
    args = _parse_args()
    session_options = {
        "date_format": args.date_format,
        "paper_size": args.paper_size,
        "font": args.font,
    }

    try:
        document_type = (
            "rirekisho"
            if args.command == "rirekisho"
            else "career_sheet"
            if args.command == "career_sheet"
            else "both"
        )
        output_target = (
            args.output if args.command in ("rirekisho", "career_sheet") else args.output_dir
        )
        markdown_content = args.markdown_file if args.command in ("career_sheet", "both") else None
        outputs = main(
            input_data=args.input_file,
            session_options=session_options,
            output_path=output_target,
            document_type=document_type,
            markdown_content=markdown_content,
        )
        output_list = outputs if isinstance(outputs, list) else [outputs]
        labels = (
            ["履歴書", "職務経歴書"]
            if args.command == "both"
            else ["履歴書" if args.command == "rirekisho" else "職務経歴書"]
        )
        for label, path in zip(labels, output_list, strict=False):
            print(f"{label}PDFを生成しました: {path}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
