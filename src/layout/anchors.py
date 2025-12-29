from __future__ import annotations

from typing import Any


def _cluster_positions(values: list[float], tol: float) -> list[float]:
    if not values:
        return []

    values = sorted(values)
    clusters: list[list[float]] = []
    for value in values:
        if not clusters or abs(value - clusters[-1][-1]) > tol:
            clusters.append([value])
        else:
            clusters[-1].append(value)

    return [round(sum(cluster) / len(cluster), 3) for cluster in clusters]


def _collect_line_positions(lines: list[dict[str, Any]], axis: str, tol: float) -> list[float]:
    if axis not in {"x", "y"}:
        raise ValueError("axis must be 'x' or 'y'")

    positions: list[float] = []
    for line in lines:
        if axis == "x":
            if abs(line["x0"] - line["x1"]) <= 0.01:
                positions.append(float(line["x0"]))
        else:
            if abs(line["y0"] - line["y1"]) <= 0.01:
                positions.append(float(line["y0"]))

    return _cluster_positions(positions, tol=tol)


def _nearest_position(value: float, positions: list[float]) -> float:
    if not positions:
        raise ValueError("No line positions found")
    return min(positions, key=lambda pos: abs(pos - value))


def build_text_anchors(
    texts: list[dict[str, Any]],
    lines: list[dict[str, Any]],
    tol: float = 0.2,
) -> list[dict[str, Any]]:
    v_positions = _collect_line_positions(lines, axis="x", tol=tol)
    h_positions = _collect_line_positions(lines, axis="y", tol=tol)

    anchors: list[dict[str, Any]] = []
    for text in texts:
        x_ref = _nearest_position(float(text["x"]), v_positions)
        y_ref = _nearest_position(float(text["y"]), h_positions)

        anchors.append(
            {
                "text": text["text"],
                "font_size": text["font_size"],
                "align": text.get("align", "left"),
                "anchor": {
                    "x_line": round(x_ref, 3),
                    "y_line": round(y_ref, 3),
                },
                "offset": {
                    "dx": round(float(text["x"]) - x_ref, 3),
                    "dy": round(float(text["y"]) - y_ref, 3),
                },
                "reference_position": {
                    "x": text["x"],
                    "y": text["y"],
                },
            }
        )

    return anchors


def resolve_texts_from_anchors(
    anchors: list[dict[str, Any]],
    lines: list[dict[str, Any]],
    tol: float = 0.2,
) -> list[dict[str, Any]]:
    v_positions = _collect_line_positions(lines, axis="x", tol=tol)
    h_positions = _collect_line_positions(lines, axis="y", tol=tol)

    resolved: list[dict[str, Any]] = []
    for anchor in anchors:
        x_line = _nearest_position(float(anchor["anchor"]["x_line"]), v_positions)
        y_line = _nearest_position(float(anchor["anchor"]["y_line"]), h_positions)
        dx = float(anchor["offset"]["dx"])
        dy = float(anchor["offset"]["dy"])

        resolved.append(
            {
                "text": anchor["text"],
                "x": round(x_line + dx, 3),
                "y": round(y_line + dy, 3),
                "font_size": anchor["font_size"],
                "align": anchor.get("align", "left"),
            }
        )

    return resolved
