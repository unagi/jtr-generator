import json
from pathlib import Path

import pytest

TOLERANCE_PT = 1.0


@pytest.fixture
def layout_data():
    layout_path = Path(__file__).parent.parent.parent / "skill/data/a4/resume_layout.json"
    with open(layout_path, encoding="utf-8") as f:
        return json.load(f)


def _closest_text(texts, expected_x, expected_y):
    return min(
        texts,
        key=lambda t: abs(t["x"] - expected_x) + abs(t["y"] - expected_y),
    )


def _assert_text_position(texts, text, expected_x, expected_y, tolerance=TOLERANCE_PT):
    candidates = [t for t in texts if t["text"] == text]
    assert candidates, f"Text not found: {text}"
    chosen = _closest_text(candidates, expected_x, expected_y)
    dx = abs(chosen["x"] - expected_x)
    dy = abs(chosen["y"] - expected_y)
    assert dx <= tolerance and dy <= tolerance, (
        f"Text '{text}' position mismatch: "
        f"expected ({expected_x}, {expected_y}), got ({chosen['x']}, {chosen['y']})"
    )


def _closest_line(lines, expected):
    return min(
        lines,
        key=lambda line: abs(line["x0"] - expected["x0"])
        + abs(line["y0"] - expected["y0"])
        + abs(line["x1"] - expected["x1"])
        + abs(line["y1"] - expected["y1"]),
    )


def _assert_line_position(lines, expected, tolerance=TOLERANCE_PT):
    chosen = _closest_line(lines, expected)
    diffs = {
        "x0": abs(chosen["x0"] - expected["x0"]),
        "y0": abs(chosen["y0"] - expected["y0"]),
        "x1": abs(chosen["x1"] - expected["x1"]),
        "y1": abs(chosen["y1"] - expected["y1"]),
    }
    assert all(diff <= tolerance for diff in diffs.values()), (
        "Line position mismatch: "
        f"expected ({expected['x0']}, {expected['y0']})-({expected['x1']}, {expected['y1']}), "
        f"got ({chosen['x0']}, {chosen['y0']})-({chosen['x1']}, {chosen['y1']})"
    )


def test_page1_label_positions(layout_data):
    page1_texts = layout_data.get("page1_texts", [])
    expected_positions = [
        ("履　歴　書", 70.46, 742.11),
        ("年　　  月 　　日現在", 294.41, 742.06),
        ("氏　　名", 71.16, 703.9),
        ("※性別", 396.53, 627.58),
        ("写真をはる位置", 453.68, 741.783),
        ("※「性別」欄：記載は任意です。未記載とすることも可能です。", 69.02, 48.09),
    ]

    for text, x, y in expected_positions:
        _assert_text_position(page1_texts, text, x, y)


def test_page2_label_positions(layout_data):
    page2_texts = layout_data.get("page2_texts", [])
    expected_positions = [
        ("学　歴・職　歴（各別にまとめて書く）", 239.8, 747.22),
        ("免　許・資　格", 300.52, 544.99),
        ("志望の動機、特技、好きな学科、アピールポイントなど", 60.0, 359.61),
        ("本人希望記入欄", 60.0, 174.54),
    ]

    for text, x, y in expected_positions:
        _assert_text_position(page2_texts, text, x, y)


def test_page1_line_positions(layout_data):
    page1_lines = layout_data.get("page1_lines", [])
    expected_lines = [
        {"x0": 66.984, "y0": 64.58, "x1": 555.914, "y1": 64.58},
        {"x0": 66.98, "y0": 64.584, "x1": 66.98, "y1": 473.474},
        {"x0": 555.91, "y0": 64.584, "x1": 555.91, "y1": 473.47},
    ]

    for expected in expected_lines:
        _assert_line_position(page1_lines, expected)


def test_page2_line_positions(layout_data):
    page2_lines = layout_data.get("page2_lines", [])
    expected_lines = [
        {"x0": 53.53, "y0": 64.58, "x1": 542.46, "y1": 64.58},
        {"x0": 53.53, "y0": 763.66, "x1": 542.46, "y1": 763.66},
        {"x0": 542.46, "y0": 64.584, "x1": 542.46, "y1": 190.46},
    ]

    for expected in expected_lines:
        _assert_line_position(page2_lines, expected)
