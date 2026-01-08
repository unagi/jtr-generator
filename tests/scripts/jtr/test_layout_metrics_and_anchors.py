from __future__ import annotations

from jtr.layout.anchors import (
    _cluster_positions,
    _collect_line_positions,
    _nearest_position,
    build_text_anchors,
    resolve_texts_from_anchors,
)
from jtr.layout.metrics import get_font_metrics


def test_cluster_positions_groups_values() -> None:
    assert _cluster_positions([], tol=0.1) == []
    clustered = _cluster_positions([10.0, 10.12, 20.0, 20.05], tol=0.2)
    assert clustered == [10.06, 20.025]


def test_collect_line_positions_validates_axis() -> None:
    lines = [
        {"x0": 1.0, "x1": 1.0, "y0": 0.0, "y1": 10.0},
        {"x0": 0.0, "x1": 10.0, "y0": 5.0, "y1": 5.0},
    ]
    v_positions = _collect_line_positions(lines, axis="x", tol=0.05)
    h_positions = _collect_line_positions(lines, axis="y", tol=0.05)

    assert v_positions == [1.0]
    assert h_positions == [5.0]

    try:
        _collect_line_positions(lines, axis="z", tol=0.05)
    except ValueError as exc:
        assert "axis must be 'x' or 'y'" in str(exc)
    else:
        raise AssertionError("ValueError was not raised for invalid axis")


def test_nearest_position_and_anchor_resolution() -> None:
    lines = [
        {"x0": 0.0, "x1": 0.0, "y0": 0.0, "y1": 10.0},
        {"x0": 10.0, "x1": 10.0, "y0": 0.0, "y1": 10.0},
        {"x0": 0.0, "x1": 10.0, "y0": 0.0, "y1": 0.0},
        {"x0": 0.0, "x1": 10.0, "y0": 10.0, "y1": 10.0},
    ]
    texts = [
        {"text": "Name", "x": 1.5, "y": 9.5, "font_size": 12, "align": "left"},
        {"text": "Address", "x": 9.4, "y": 0.6, "font_size": 10, "align": "right"},
    ]

    anchors = build_text_anchors(texts, lines, tol=0.1)
    resolved = resolve_texts_from_anchors(anchors, lines, tol=0.1)

    assert anchors[0]["anchor"] == {"x_line": 0.0, "y_line": 10.0}
    assert anchors[1]["anchor"] == {"x_line": 10.0, "y_line": 0.0}
    assert resolved == [
        {"text": "Name", "x": 1.5, "y": 9.5, "font_size": 12, "align": "left"},
        {"text": "Address", "x": 9.4, "y": 0.6, "font_size": 10, "align": "right"},
    ]

    try:
        _nearest_position(1.0, [])
    except ValueError as exc:
        assert "No line positions found" in str(exc)
    else:
        raise AssertionError("ValueError was not raised for empty positions")


def test_get_font_metrics_uses_reportlab_defaults() -> None:
    metrics = get_font_metrics("Helvetica", 12)
    assert set(metrics) == {"ascent", "descent", "height"}
    assert metrics["ascent"] > 0
    assert metrics["height"] == metrics["ascent"] - metrics["descent"]
