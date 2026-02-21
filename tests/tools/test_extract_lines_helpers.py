from __future__ import annotations

from types import SimpleNamespace

from tools import extract_lines as el


def _style() -> el.DrawingStyle:
    return el.DrawingStyle(
        stroke_width=1.0,
        dash_pattern=[],
        dash_phase=0.0,
        line_cap=0,
        line_join=0,
        color=[0.0, 0.0, 0.0],
    )


def test_resolve_line_cap_and_join() -> None:
    cap, next_cap = el._resolve_line_cap(None, 1)
    assert cap == 1
    assert next_cap == 1

    cap, next_cap = el._resolve_line_cap((2, 2, 2), 0)
    assert cap == 2
    assert next_cap == 2

    join, next_join = el._resolve_line_join(None, 1)
    assert join == 1
    assert next_join == 1

    join, next_join = el._resolve_line_join(2, 0)
    assert join == 2
    assert next_join == 2


def test_segments_from_item_line_and_rect() -> None:
    style = _style()
    p1 = SimpleNamespace(x=1.0, y=2.0)
    p2 = SimpleNamespace(x=3.0, y=4.0)
    line_segments = el._segments_from_item(("l", p1, p2), style)
    assert len(line_segments) == 1
    assert line_segments[0][:4] == (1.0, 2.0, 3.0, 4.0)

    rect = SimpleNamespace(x0=0.0, y0=0.0, x1=2.0, y1=1.0)
    rect_segments = el._segments_from_item(("re", rect), style)
    assert len(rect_segments) == 4
    assert rect_segments[0][:4] == (0.0, 0.0, 2.0, 0.0)
    assert rect_segments[3][:4] == (0.0, 1.0, 0.0, 0.0)


def test_resolve_drawing_style() -> None:
    drawing = {
        "width": None,
        "dashes": "[3 3] 1",
        "lineCap": (2, 2, 2),
        "lineJoin": 1,
        "color": (0.1, 0.2, 0.3),
    }
    style, next_cap, next_join = el._resolve_drawing_style(drawing, 0, 0)
    assert style.stroke_width == 1.0
    assert style.dash_pattern == [3.0, 3.0]
    assert style.dash_phase == 1.0
    assert style.line_cap == 2
    assert style.line_join == 1
    assert style.color == [0.1, 0.2, 0.3]
    assert next_cap == 2
    assert next_join == 1
