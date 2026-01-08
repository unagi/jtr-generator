#!/usr/bin/env python3
"""職務経歴書PDF生成の手動テストスクリプト。

開発者がローカルで職務経歴書生成を試すための補助ツールです。
生成結果は``outputs/test_career_sheet.pdf``に出力されます。
"""

from __future__ import annotations

from pathlib import Path

import main as skill_main

SAMPLE_RIREKISHO = Path("skill/assets/examples/sample_rirekisho.yaml")
SAMPLE_MARKDOWN = Path("skill/assets/examples/sample_career_content.md")


def _print_context(output_path: Path) -> None:
    print("職務経歴書PDF生成テスト")
    print(f"履歴書データ: {SAMPLE_RIREKISHO}")
    print(f"Markdown: {SAMPLE_MARKDOWN}")
    print(f"出力先: {output_path}\n")


def _generate(output_path: Path) -> Path:
    return skill_main.main(
        input_data=SAMPLE_RIREKISHO,
        document_type="career_sheet",
        markdown_content=SAMPLE_MARKDOWN,
        output_path=output_path,
    )


def main() -> int:
    output_path = Path("outputs/test_career_sheet.pdf")
    output_path.parent.mkdir(exist_ok=True)

    _print_context(output_path)
    try:
        result_path = _generate(output_path)
    except Exception as exc:  # noqa: BLE001 - ユーティリティスクリプトのため集約
        print(f"❌ エラー: {exc}")
        return 1

    print(f"✅ 職務経歴書PDFを生成しました: {result_path}")
    size = result_path.stat().st_size
    print(f"   ファイルサイズ: {size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
