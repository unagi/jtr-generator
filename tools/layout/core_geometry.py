from __future__ import annotations

from typing import Any, Literal

Axis = Literal["x", "y"]


def collect_line_positions(
    lines: list[dict[str, Any]],
    axis: Axis,
    *,
    line_tolerance: float = 0.01,
    round_digits: int = 3,
) -> list[float]:
    if axis not in {"x", "y"}:
        raise ValueError("axis must be 'x' or 'y'")

    positions: list[float] = []
    for line in lines:
        if axis == "x":
            if abs(line["x0"] - line["x1"]) <= line_tolerance:
                positions.append(float(line["x0"]))
        else:
            if abs(line["y0"] - line["y1"]) <= line_tolerance:
                positions.append(float(line["y0"]))

    return sorted({round(pos, round_digits) for pos in positions})


def nearest_bounds(value: float, positions: list[float]) -> tuple[float | None, float | None]:
    below = [pos for pos in positions if pos <= value]
    above = [pos for pos in positions if pos >= value]
    return (max(below) if below else None, min(above) if above else None)


def nearest_left(value: float, positions: list[float]) -> float | None:
    lefts = [pos for pos in positions if pos <= value]
    return max(lefts) if lefts else None


def expected_baseline(
    valign: str,
    bottom: float | None,
    top: float | None,
    metrics: dict[str, float],
    margin_top: float | None = None,
    margin_bottom: float | None = None,
) -> float | None:
    if bottom is None or top is None:
        return None

    if valign == "center":
        center = bottom + (top - bottom) / 2
        return center - (metrics["ascent"] + metrics["descent"]) / 2
    if valign == "top":
        margin = margin_top or 0.0
        return top - metrics["ascent"] - margin
    if valign == "bottom":
        margin = margin_bottom or 0.0
        return bottom - metrics["descent"] + margin
    return None
