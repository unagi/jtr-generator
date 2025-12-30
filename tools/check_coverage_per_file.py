#!/usr/bin/env python3
"""個別ファイルのカバレッジ最低値チェック

全体のカバレッジ基準に加えて、個別ファイルごとの最低値を検証します。
pytest-covが生成したcoverage.xmlを解析して、基準を満たさないファイルを報告します。
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def check_file_coverage(
    coverage_xml_path: Path,
    min_coverage: float = 80.0,
    exclude_files: list[str] | None = None,
) -> tuple[bool, list[tuple[str, float]]]:
    """
    coverage.xmlを解析して個別ファイルのカバレッジをチェック

    Args:
        coverage_xml_path: coverage.xmlファイルのパス
        min_coverage: 最低カバレッジ率（デフォルト: 80.0%）
        exclude_files: 除外するファイルパターンのリスト

    Returns:
        (全ファイルが基準を満たしているか, 基準未達のファイルリスト)
    """
    if not coverage_xml_path.exists():
        print(f"エラー: {coverage_xml_path} が見つかりません", file=sys.stderr)
        return False, []

    exclude_files = exclude_files or []
    tree = ET.parse(coverage_xml_path)
    root = tree.getroot()

    failing_files: list[tuple[str, float]] = []

    # packages要素を探索
    for package in root.findall(".//package"):
        for cls in package.findall("classes/class"):
            filename = cls.get("filename", "")
            line_rate = float(cls.get("line-rate", "0"))
            coverage_percent = line_rate * 100

            # 除外パターンチェック
            should_exclude = any(pattern in filename for pattern in exclude_files)
            if should_exclude:
                continue

            # 最低基準未達をリストに追加
            if coverage_percent < min_coverage:
                failing_files.append((filename, coverage_percent))

    return len(failing_files) == 0, failing_files


def main() -> int:
    """メイン関数"""
    coverage_xml = Path("coverage.xml")
    min_coverage = 80.0

    # __init__.pyとチェックスクリプト自身を除外
    exclude_patterns = ["__init__.py", "check_coverage_per_file.py"]

    all_passed, failing_files = check_file_coverage(coverage_xml, min_coverage, exclude_patterns)

    if all_passed:
        print(f"✅ 全ファイルが最低カバレッジ {min_coverage}% を満たしています")
        return 0

    print(f"❌ 以下のファイルがカバレッジ {min_coverage}% を下回っています:\n")
    for filename, coverage in sorted(failing_files, key=lambda x: x[1]):
        print(f"  {filename}: {coverage:.2f}%")

    print(f"\n合計 {len(failing_files)} ファイルが基準未達です。テストを追加してください。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
