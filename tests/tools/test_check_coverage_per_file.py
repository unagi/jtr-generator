"""Tests for tools.check_coverage_per_file module"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from tools.check_coverage_per_file import check_file_coverage


def _write_coverage_xml(tmp_path: Path, xml: str) -> Path:
    """テスト用にcoverage.xmlを作成"""
    path = tmp_path / "coverage.xml"
    path.write_text(xml, encoding="utf-8")
    return path


def test_all_files_pass_threshold(tmp_path: Path) -> None:
    """全ファイルが基準を満たす場合"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/foo.py" line-rate="0.85"/>
        <class filename="skill/bar.py" line-rate="0.90"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)
    assert failing == []


def test_some_files_below_threshold(tmp_path: Path) -> None:
    """一部ファイルが基準未達の場合"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/foo.py" line-rate="0.79"/>
        <class filename="skill/bar.py" line-rate="0.90"/>
        <class filename="skill/baz.py" line-rate="0.50"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)
    assert len(failing) == 2
    assert failing == [("skill/foo.py", 79.0), ("skill/baz.py", 50.0)]


def test_exclude_filenames(tmp_path: Path) -> None:
    """除外ファイル名が正しく機能する"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/__init__.py" line-rate="0.0"/>
        <class filename="skill/foo.py" line-rate="0.79"/>
        <class filename="tools/check_coverage_per_file.py" line-rate="0.0"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(
        _write_coverage_xml(tmp_path, xml),
        min_coverage=80.0,
        exclude_filenames={"__init__.py", "check_coverage_per_file.py"},
    )
    assert len(failing) == 1
    assert failing == [("skill/foo.py", 79.0)]


def test_file_not_found(tmp_path: Path) -> None:
    """coverage.xmlが存在しない場合"""
    nonexistent = tmp_path / "nonexistent.xml"
    with pytest.raises(FileNotFoundError, match="が見つかりません"):
        check_file_coverage(nonexistent, min_coverage=80.0)


def test_invalid_xml(tmp_path: Path) -> None:
    """不正なXMLの場合"""
    xml = "<<invalid xml>>"
    with pytest.raises(ET.ParseError):
        check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)


def test_missing_line_rate_attribute(tmp_path: Path) -> None:
    """line-rate属性が欠落している場合"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/foo.py"/>
        <class filename="skill/bar.py" line-rate="0.90"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)
    # line-rate属性がないファイルはスキップ
    assert failing == []


def test_invalid_line_rate_value(tmp_path: Path) -> None:
    """line-rate属性が無効な値の場合"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/foo.py" line-rate="invalid"/>
        <class filename="skill/bar.py" line-rate="0.79"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)
    # 無効な値はスキップ
    assert len(failing) == 1
    assert failing == [("skill/bar.py", 79.0)]


def test_empty_coverage_xml(tmp_path: Path) -> None:
    """空のcoverage.xmlの場合"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
  </packages>
</coverage>
"""
    failing = check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)
    assert failing == []


def test_exact_threshold(tmp_path: Path) -> None:
    """閾値ちょうどの場合は合格"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/foo.py" line-rate="0.80"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(_write_coverage_xml(tmp_path, xml), min_coverage=80.0)
    assert failing == []


def test_exclude_filenames_none(tmp_path: Path) -> None:
    """exclude_filenames=Noneの場合"""
    xml = """<?xml version="1.0"?>
<coverage>
  <packages>
    <package name="pkg">
      <classes>
        <class filename="skill/__init__.py" line-rate="0.0"/>
      </classes>
    </package>
  </packages>
</coverage>
"""
    failing = check_file_coverage(
        _write_coverage_xml(tmp_path, xml), min_coverage=80.0, exclude_filenames=None
    )
    assert len(failing) == 1
    assert failing == [("skill/__init__.py", 0.0)]
