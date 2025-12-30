#!/usr/bin/env python3
"""個別ファイルのカバレッジ最低値チェック

全体のカバレッジ基準に加えて、個別ファイルごとの最低値を検証します。
pytest-covが生成したcoverage.xmlを解析して、基準を満たさないファイルを報告します。
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath


def check_file_coverage(
    coverage_xml_path: Path,
    min_coverage: float = 80.0,
    exclude_filenames: set[str] | None = None,
) -> list[tuple[str, float]]:
    """
    coverage.xmlを解析して個別ファイルのカバレッジをチェック

    Args:
        coverage_xml_path: coverage.xmlファイルのパス
        min_coverage: 最低カバレッジ率（デフォルト: 80.0%）
        exclude_filenames: 除外するファイル名のセット（完全一致）

    Returns:
        基準未達のファイルリスト [(filepath, coverage_percent), ...]

    Raises:
        FileNotFoundError: coverage.xmlが存在しない場合
        ET.ParseError: XMLパースに失敗した場合
        ValueError: 無効なXML構造の場合
    """
    if not coverage_xml_path.exists():
        raise FileNotFoundError(f"{coverage_xml_path} が見つかりません")

    exclude_filenames = exclude_filenames or set()
    tree = ET.parse(coverage_xml_path)
    root = tree.getroot()

    failing_files: list[tuple[str, float]] = []

    # packages要素を探索
    for package in root.findall(".//package"):
        for cls in package.findall("classes/class"):
            filename = cls.get("filename", "")
            line_rate_str = cls.get("line-rate")

            if not line_rate_str:
                continue

            try:
                line_rate = float(line_rate_str)
            except ValueError:
                continue

            coverage_percent = line_rate * 100

            # 除外判定（ファイル名の完全一致）
            file_basename = PurePosixPath(filename).name
            if file_basename in exclude_filenames:
                continue

            # 最低基準未達をリストに追加
            if coverage_percent < min_coverage:
                failing_files.append((filename, coverage_percent))

    return failing_files


def main() -> int:
    """メイン関数"""
    coverage_xml = Path("coverage.xml")
    min_coverage = 80.0

    # __init__.pyとチェックスクリプト自身を除外（ファイル名完全一致）
    exclude_filenames = {"__init__.py", "check_coverage_per_file.py"}

    try:
        failing_files = check_file_coverage(coverage_xml, min_coverage, exclude_filenames)
    except (FileNotFoundError, ET.ParseError, ValueError, OSError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2

    if not failing_files:
        print(f"OK: 全ファイルが最低カバレッジ {min_coverage}% を満たしています")
        return 0

    print(f"NG: 以下のファイルがカバレッジ {min_coverage}% を下回っています:\n")
    for filename, coverage in sorted(failing_files, key=lambda x: x[1]):
        print(f"  {filename}: {coverage:.2f}%")

    print(f"\n合計 {len(failing_files)} ファイルが基準未達です。テストを追加してください。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
