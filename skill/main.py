from __future__ import annotations

import sys
from argparse import ArgumentParser
from importlib import util
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skill.scripts import main as scripts_main
elif util.find_spec("skill.scripts.main") is not None:
    from skill.scripts import main as scripts_main
else:
    from scripts import main as scripts_main

__all__ = ["main"]


def main(
    input_data: str | Path,
    session_options: dict[str, Any] | None = None,
    output_path: Path | str | None = None,
    document_type: str = "resume",
    markdown_content: str | Path | None = None,
    additional_info: str | Path | None = None,
) -> Path:
    """Skill配布物のエントリーポイント（scripts/main.pyのラッパー）。"""
    return scripts_main.main(
        input_data=input_data,
        session_options=session_options,
        output_path=output_path,
        document_type=document_type,
        markdown_content=markdown_content,
        additional_info=additional_info,
    )


def _parse_args() -> tuple[Path, dict[str, str]]:
    parser = ArgumentParser(description="日本の履歴書PDF生成")
    parser.add_argument("input_file", type=Path, help="入力YAMLまたはJSONファイル")
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
    args = parser.parse_args()

    session_options = {"date_format": args.date_format, "paper_size": args.paper_size}
    return args.input_file, session_options


if __name__ == "__main__":
    input_file, options = _parse_args()
    try:
        output = main(input_file, options)
        print(f"履歴書PDFを生成しました: {output}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
