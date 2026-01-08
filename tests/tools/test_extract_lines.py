"""
罫線データ抽出機能のテスト

このテストは以下を検証します:
1. JSON Schemaへの適合性
2. 線分数の一致
3. 線幅の統計分布
4. 座標の妥当性
5. 二重線パターンの検出
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")


@pytest.fixture
def layout_data():
    """v2レイアウトデータを読み込む"""
    layout_path = (
        Path(__file__).parent.parent.parent
        / "jtr-generator"
        / "assets"
        / "data"
        / "a4"
        / "rirekisho_layout.json"
    )
    with open(layout_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def layout_schema():
    """レイアウトスキーマを読み込む"""
    schema_path = Path(__file__).parent.parent.parent / "tools" / "schema" / "layout_schema.json"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def test_layout_json_schema_validation(layout_data, layout_schema):
    """JSON Schemaに準拠していることを確認"""
    # スキーマバリデーション実行
    jsonschema.validate(layout_data, layout_schema)


def test_line_count_matches_reference(layout_data):
    """参照PDFの線分数と一致することを確認"""
    page1_count = len(layout_data["page1_lines"])
    page2_count = len(layout_data["page2_lines"])
    total = page1_count + page2_count

    # 期待値: 208本（実測値）
    assert total == 208, (
        f"Expected 208 lines, got {total} (page1: {page1_count}, page2: {page2_count})"
    )


def test_line_width_distribution(layout_data):
    """線幅の統計分布が参照PDFと一致することを確認"""
    widths = []
    for page_lines in [layout_data["page1_lines"], layout_data["page2_lines"]]:
        for line in page_lines:
            widths.append(line["width"])

    # 線幅の度数分布
    width_counts = Counter(widths)

    # 期待値（実測値: 0.14pt: 66本、1.0pt: 138本、0.75pt: 4本）
    # マージロジックにより多少の変動があるため、許容誤差を設ける
    expected_ranges = {
        0.14: (60, 70),  # 細線（二重線の中心）
        1.0: (130, 145),  # 太線（二重線の外枠、通常罫線）
        0.75: (3, 5),  # 証明写真枠
    }

    for width, (min_count, max_count) in expected_ranges.items():
        actual_count = width_counts.get(width, 0)
        assert min_count <= actual_count <= max_count, (
            f"Width {width}pt: expected {min_count}-{max_count}, got {actual_count}"
        )


def test_coordinates_validity(layout_data):
    """座標がA4範囲内かつ有効な値であることを確認"""
    A4_WIDTH = 595.276  # pt
    A4_HEIGHT = 841.890  # pt

    for page_name in ["page1_lines", "page2_lines"]:
        page_lines = layout_data[page_name]
        for i, line in enumerate(page_lines):
            # NaN/Infチェック
            assert math.isfinite(line["x0"]), f"{page_name}[{i}]: x0 is not finite"
            assert math.isfinite(line["y0"]), f"{page_name}[{i}]: y0 is not finite"
            assert math.isfinite(line["x1"]), f"{page_name}[{i}]: x1 is not finite"
            assert math.isfinite(line["y1"]), f"{page_name}[{i}]: y1 is not finite"

            # A4範囲内チェック（余裕を持たせて-10 ~ +10）
            for coord, name in [(line["x0"], "x0"), (line["x1"], "x1")]:
                assert -10 <= coord <= A4_WIDTH + 10, (
                    f"{page_name}[{i}]: {name}={coord} out of A4 width range"
                )

            for coord, name in [(line["y0"], "y0"), (line["y1"], "y1")]:
                assert -10 <= coord <= A4_HEIGHT + 10, (
                    f"{page_name}[{i}]: {name}={coord} out of A4 height range"
                )

            # 線幅が正の値であることを確認
            assert line["width"] > 0, f"{page_name}[{i}]: width must be positive"

            # cap/joinが有効な値であることを確認
            assert 0 <= line["cap"] <= 2, f"{page_name}[{i}]: cap must be 0-2"
            assert 0 <= line["join"] <= 2, f"{page_name}[{i}]: join must be 0-2"

            # colorが有効な値であることを確認
            assert len(line["color"]) == 3, f"{page_name}[{i}]: color must have 3 elements"
            for c in line["color"]:
                assert 0.0 <= c <= 1.0, f"{page_name}[{i}]: color values must be 0.0-1.0"


def test_double_line_pattern_detection(layout_data):
    """二重線の3本セットパターンが検出されることを確認"""
    # page1の水平線のみをチェック（y0 == y1）
    horizontal_lines = [
        line for line in layout_data["page1_lines"] if abs(line["y0"] - line["y1"]) < 0.1
    ]

    # y座標でグループ化（0.1pt精度で近接する線をグループ化）
    by_y = defaultdict(list)
    for line in horizontal_lines:
        y_key = round(line["y0"], 1)
        by_y[y_key].append(line)

    # 二重線パターン（太-細-太）を探す
    # 二重線は同じy座標付近に3本の線（1.0pt, 0.14pt, 1.0pt）が存在する
    double_line_groups = 0
    for _y, lines in by_y.items():
        widths = [line["width"] for line in lines]
        width_counts = Counter(widths)
        # 0.14が1本以上、1.0が2本以上含まれていればそのグループは二重線
        if width_counts.get(0.14, 0) >= 1 and width_counts.get(1.0, 0) >= 2:
            double_line_groups += 1

    # JIS規格の履歴書では少なくとも1組の二重線が存在する（検証として）
    assert double_line_groups >= 1, (
        f"Expected at least 1 double-line group, found {double_line_groups}"
    )


def test_line_attributes_completeness(layout_data):
    """すべての線に必要な属性が含まれていることを確認"""
    required_fields = [
        "x0",
        "y0",
        "x1",
        "y1",
        "width",
        "dash_pattern",
        "dash_phase",
        "cap",
        "join",
        "color",
    ]

    for page_name in ["page1_lines", "page2_lines"]:
        page_lines = layout_data[page_name]
        for i, line in enumerate(page_lines):
            for field in required_fields:
                assert field in line, f"{page_name}[{i}]: missing field '{field}'"


def test_dash_pattern_consistency(layout_data):
    """破線パターンが一貫していることを確認"""
    # 参照PDFには少数の破線パターン（[2.25, 0.75]）が含まれる
    dash_patterns = set()

    for page_name in ["page1_lines", "page2_lines"]:
        page_lines = layout_data[page_name]
        for i, line in enumerate(page_lines):
            assert isinstance(line["dash_pattern"], list), (
                f"{page_name}[{i}]: dash_pattern must be a list"
            )
            assert isinstance(line["dash_phase"], (int, float)), (
                f"{page_name}[{i}]: dash_phase must be a number"
            )

            # dash_patternを収集
            pattern_tuple = tuple(line["dash_pattern"])
            dash_patterns.add(pattern_tuple)

    # 期待されるパターン: 実線 [] と破線 [2.25, 0.75]
    expected_patterns = {(), (2.25, 0.75)}
    assert dash_patterns == expected_patterns, (
        f"Expected dash patterns {expected_patterns}, got {dash_patterns}"
    )


def test_source_page_size(layout_data):
    """元のPDFページサイズが正しいことを確認"""
    source_size = layout_data["source_page_size_pt"]
    expected_width = 1190.52  # A3横の幅
    expected_height = 841.92  # A3横の高さ

    assert abs(source_size[0] - expected_width) < 1.0, (
        f"Expected source width ~{expected_width}, got {source_size[0]}"
    )
    assert abs(source_size[1] - expected_height) < 1.0, (
        f"Expected source height ~{expected_height}, got {source_size[1]}"
    )


def test_split_position(layout_data):
    """A3の分割位置が中央であることを確認"""
    split_x = layout_data["split_x_pt"]
    source_width = layout_data["source_page_size_pt"][0]
    expected_split = source_width / 2

    assert abs(split_x - expected_split) < 1.0, (
        f"Expected split at ~{expected_split}, got {split_x}"
    )
