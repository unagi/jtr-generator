from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

RawSegment = tuple[
    float,
    float,
    float,
    float,
    float,
    list[float],
    float,
    int,
    int,
    list[float],
]
HorizontalSegment = tuple[
    float,
    float,
    float,
    float,
    list[float],
    float,
    int,
    int,
    list[float],
]
VerticalSegment = tuple[
    float,
    float,
    float,
    float,
    list[float],
    float,
    int,
    int,
    list[float],
]
MergeInterval = tuple[float, float, float, list[float], float, int, int, list[float]]


@dataclass(frozen=True)
class LineExtractionConfig:
    line_detection_tolerance_pt: float = 0.1
    minimum_line_length_pt: float = 0.5
    split_tolerance_pt: float = 0.5
    merge_tolerance_pt: float = 1.2
    position_round_digits: int = 3
    line_width_round_digits: int = 3


@dataclass(frozen=True)
class DrawingStyle:
    stroke_width: float
    dash_pattern: list[float]
    dash_phase: float
    line_cap: int
    line_join: int
    color: list[float]


def _default_config_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "jtr-generator"
        / "assets"
        / "data"
        / "a4"
        / "definitions"
        / "line_extraction_config.json"
    )


def _load_extraction_config(config_path: Path | None = None) -> LineExtractionConfig:
    path = config_path or _default_config_path()
    if not path.exists():
        return LineExtractionConfig()

    with open(path, encoding="utf-8") as f:
        loaded = json.load(f)

    if not isinstance(loaded, dict):
        raise ValueError(f"Invalid extraction config format: {path}")

    defaults = LineExtractionConfig()
    return LineExtractionConfig(
        line_detection_tolerance_pt=float(
            loaded.get("line_detection_tolerance_pt", defaults.line_detection_tolerance_pt)
        ),
        minimum_line_length_pt=float(
            loaded.get("minimum_line_length_pt", defaults.minimum_line_length_pt)
        ),
        split_tolerance_pt=float(loaded.get("split_tolerance_pt", defaults.split_tolerance_pt)),
        merge_tolerance_pt=float(loaded.get("merge_tolerance_pt", defaults.merge_tolerance_pt)),
        position_round_digits=int(
            loaded.get("position_round_digits", defaults.position_round_digits)
        ),
        line_width_round_digits=int(
            loaded.get("line_width_round_digits", defaults.line_width_round_digits)
        ),
    )


def _parse_dashes(dashes_str: str) -> tuple[list[float], float]:
    """
    PyMuPDFのdashes文字列をパースする

    Args:
        dashes_str: PyMuPDFのdashes文字列（例: "[] 0", "[3 3] 0"）

    Returns:
        (dash_pattern, dash_phase) のタプル
    """
    match = re.match(r"\[([\d\s.]*)\]\s*([\d.]+)", dashes_str.strip())
    if not match:
        return [], 0

    pattern_str, phase_str = match.groups()
    pattern = [float(x) for x in pattern_str.split()] if pattern_str.strip() else []
    phase = float(phase_str)
    return pattern, phase


def _merge_intervals(intervals: list[MergeInterval], tol: float) -> list[MergeInterval]:
    """同一直線上で分割された線分を結合する。"""
    sorted_intervals = sorted(intervals, key=lambda item: (item[0], item[1]))
    merged: list[list[Any]] = []

    for item in sorted_intervals:
        s, e, w, dash_pat, dash_ph, cap, join, color = item
        if not merged:
            merged.append([s, e, w, dash_pat, dash_ph, cap, join, color])
            continue

        ps, pe, pw, p_dash_pat, p_dash_ph, p_cap, p_join, p_color = merged[-1]
        # 線幅と描画属性が同じ場合のみ結合
        if (
            s <= pe + tol
            and abs(w - pw) < 0.01
            and dash_pat == p_dash_pat
            and dash_ph == p_dash_ph
            and cap == p_cap
            and join == p_join
            and color == p_color
        ):
            merged[-1][1] = max(pe, e)
        else:
            merged.append([s, e, w, dash_pat, dash_ph, cap, join, color])

    return [
        (s, e, w, dash_pat, dash_ph, cap, join, color)
        for s, e, w, dash_pat, dash_ph, cap, join, color in merged
    ]


def _resolve_line_cap(line_cap_raw: Any, last_cap: int) -> tuple[int, int]:
    if line_cap_raw is None:
        return last_cap, last_cap
    if isinstance(line_cap_raw, tuple):
        resolved = int(line_cap_raw[0])
        return resolved, resolved
    resolved = int(line_cap_raw)
    return resolved, resolved


def _resolve_line_join(line_join_raw: Any, last_join: int) -> tuple[int, int]:
    if line_join_raw is None:
        return last_join, last_join
    resolved = int(line_join_raw)
    return resolved, resolved


def _resolve_color(color_tuple: Any) -> list[float]:
    return [0.0, 0.0, 0.0] if color_tuple is None else list(color_tuple)


def _resolve_drawing_style(
    drawing: dict[str, Any], last_cap: int, last_join: int
) -> tuple[DrawingStyle, int, int]:
    stroke_width = drawing.get("width", 1.0) or 1.0
    dash_pattern, dash_phase = _parse_dashes(drawing.get("dashes") or "[] 0")
    line_cap, next_cap = _resolve_line_cap(drawing.get("lineCap"), last_cap)
    line_join, next_join = _resolve_line_join(drawing.get("lineJoin"), last_join)
    color = _resolve_color(drawing.get("color"))
    style = DrawingStyle(
        stroke_width=stroke_width,
        dash_pattern=dash_pattern,
        dash_phase=dash_phase,
        line_cap=line_cap,
        line_join=line_join,
        color=color,
    )
    return style, next_cap, next_join


def _line_segment(x0: float, y0: float, x1: float, y1: float, style: DrawingStyle) -> RawSegment:
    return (
        x0,
        y0,
        x1,
        y1,
        style.stroke_width,
        style.dash_pattern,
        style.dash_phase,
        style.line_cap,
        style.line_join,
        style.color,
    )


def _rect_segments(rect: Any, style: DrawingStyle) -> list[RawSegment]:
    return [
        _line_segment(rect.x0, rect.y0, rect.x1, rect.y0, style),
        _line_segment(rect.x1, rect.y0, rect.x1, rect.y1, style),
        _line_segment(rect.x1, rect.y1, rect.x0, rect.y1, style),
        _line_segment(rect.x0, rect.y1, rect.x0, rect.y0, style),
    ]


def _segments_from_item(item: tuple[Any, ...], style: DrawingStyle) -> list[RawSegment]:
    op = item[0]
    if op == "l":
        p1, p2 = item[1], item[2]
        return [_line_segment(p1.x, p1.y, p2.x, p2.y, style)]
    if op == "re":
        return _rect_segments(item[1], style)
    return []


def _extract_raw_segments(page: fitz.Page) -> tuple[list[RawSegment], float, float]:
    width, height = page.rect.width, page.rect.height
    last_cap = 0  # PDF初期値: butt cap
    last_join = 0  # PDF初期値: mitre join
    segments: list[RawSegment] = []

    for drawing in page.get_drawings():
        style, last_cap, last_join = _resolve_drawing_style(drawing, last_cap, last_join)
        for item in drawing["items"]:
            segments.extend(_segments_from_item(item, style))

    return segments, width, height


def _classify_segments(
    segments: list[RawSegment], config: LineExtractionConfig
) -> tuple[list[HorizontalSegment], list[VerticalSegment]]:
    horizontal: list[HorizontalSegment] = []
    vertical: list[VerticalSegment] = []

    for x0, y0, x1, y1, width, dash_pat, dash_ph, cap, join, color in segments:
        if (
            abs(y0 - y1) < config.line_detection_tolerance_pt
            and abs(x0 - x1) > config.minimum_line_length_pt
        ):
            horizontal.append(
                (min(x0, x1), y0, max(x0, x1), width, dash_pat, dash_ph, cap, join, color)
            )
        elif (
            abs(x0 - x1) < config.line_detection_tolerance_pt
            and abs(y0 - y1) > config.minimum_line_length_pt
        ):
            vertical.append(
                (x0, min(y0, y1), max(y0, y1), width, dash_pat, dash_ph, cap, join, color)
            )

    return horizontal, vertical


def _split_segments_for_pages(
    horizontal: list[HorizontalSegment],
    vertical: list[VerticalSegment],
    split_x: float,
    config: LineExtractionConfig,
) -> tuple[
    list[HorizontalSegment], list[HorizontalSegment], list[VerticalSegment], list[VerticalSegment]
]:
    tol = config.split_tolerance_pt
    left_h = [segment for segment in horizontal if segment[2] <= split_x + tol]
    right_h = [segment for segment in horizontal if segment[0] >= split_x - tol]
    left_v = [segment for segment in vertical if segment[0] <= split_x + tol]
    right_v = [segment for segment in vertical if segment[0] >= split_x - tol]
    return left_h, right_h, left_v, right_v


def _group_horizontal_segments(
    horizontal_segments: list[HorizontalSegment], x_shift: float
) -> dict[tuple[Any, ...], list[tuple[float, float]]]:
    grouped: dict[tuple[Any, ...], list[tuple[float, float]]] = defaultdict(list)
    for x0, y, x1, width, dash_pat, dash_ph, cap, join, color in horizontal_segments:
        y_key = round(y, 2)
        attr_key = (y_key, round(width, 3), tuple(dash_pat), dash_ph, cap, join, tuple(color))
        grouped[attr_key].append((x0 - x_shift, x1 - x_shift))
    return grouped


def _group_vertical_segments(
    vertical_segments: list[VerticalSegment],
) -> dict[tuple[Any, ...], list[tuple[float, float]]]:
    grouped: dict[tuple[Any, ...], list[tuple[float, float]]] = defaultdict(list)
    for x, y0, y1, width, dash_pat, dash_ph, cap, join, color in vertical_segments:
        x_key = round(x, 2)
        attr_key = (x_key, round(width, 3), tuple(dash_pat), dash_ph, cap, join, tuple(color))
        grouped[attr_key].append((y0, y1))
    return grouped


def _build_horizontal_lines(
    grouped: dict[tuple[Any, ...], list[tuple[float, float]]],
    page_height: float,
    config: LineExtractionConfig,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for (y_key, width, dash_pat_tuple, dash_ph, cap, join, color_tuple), xs in grouped.items():
        dash_pat = list(dash_pat_tuple)
        color = list(color_tuple)
        intervals: list[MergeInterval] = [
            (min(a, b), max(a, b), width, dash_pat, dash_ph, cap, join, color) for a, b in xs
        ]
        merged = _merge_intervals(intervals, tol=config.merge_tolerance_pt)
        for (
            s,
            e,
            merged_width,
            merged_dash_pat,
            merged_dash_ph,
            merged_cap,
            merged_join,
            merged_color,
        ) in merged:
            y_rl = page_height - y_key
            out.append(
                {
                    "x0": s,
                    "y0": y_rl,
                    "x1": e,
                    "y1": y_rl,
                    "width": merged_width,
                    "dash_pattern": merged_dash_pat,
                    "dash_phase": merged_dash_ph,
                    "cap": merged_cap,
                    "join": merged_join,
                    "color": merged_color,
                }
            )
    return out


def _build_vertical_lines(
    grouped: dict[tuple[Any, ...], list[tuple[float, float]]],
    page_height: float,
    x_shift: float,
    config: LineExtractionConfig,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for (x_key, width, dash_pat_tuple, dash_ph, cap, join, color_tuple), ys in grouped.items():
        dash_pat = list(dash_pat_tuple)
        color = list(color_tuple)
        intervals: list[MergeInterval] = [
            (min(a, b), max(a, b), width, dash_pat, dash_ph, cap, join, color) for a, b in ys
        ]
        merged = _merge_intervals(intervals, tol=config.merge_tolerance_pt)
        for (
            s,
            e,
            merged_width,
            merged_dash_pat,
            merged_dash_ph,
            merged_cap,
            merged_join,
            merged_color,
        ) in merged:
            x_rl = x_key - x_shift
            y0_rl = page_height - e
            y1_rl = page_height - s
            out.append(
                {
                    "x0": x_rl,
                    "y0": y0_rl,
                    "x1": x_rl,
                    "y1": y1_rl,
                    "width": merged_width,
                    "dash_pattern": merged_dash_pat,
                    "dash_phase": merged_dash_ph,
                    "cap": merged_cap,
                    "join": merged_join,
                    "color": merged_color,
                }
            )
    return out


def _round_and_sort_lines(
    lines: list[dict[str, Any]], config: LineExtractionConfig
) -> list[dict[str, Any]]:
    for line in lines:
        line["x0"] = round(line["x0"], config.position_round_digits)
        line["y0"] = round(line["y0"], config.position_round_digits)
        line["x1"] = round(line["x1"], config.position_round_digits)
        line["y1"] = round(line["y1"], config.position_round_digits)
        line["width"] = round(line["width"], config.line_width_round_digits)
    lines.sort(key=lambda row: (row["y0"], row["x0"], row["y1"], row["x1"]))
    return lines


def _to_reportlab_lines(
    horizontal_segments: list[HorizontalSegment],
    vertical_segments: list[VerticalSegment],
    page_height: float,
    x_shift: float,
    config: LineExtractionConfig,
) -> list[dict[str, Any]]:
    horizontal_grouped = _group_horizontal_segments(horizontal_segments, x_shift)
    vertical_grouped = _group_vertical_segments(vertical_segments)
    lines = _build_horizontal_lines(horizontal_grouped, page_height, config)
    lines.extend(_build_vertical_lines(vertical_grouped, page_height, x_shift, config))
    return _round_and_sort_lines(lines, config)


def extract_lines_a3_to_a4x2(pdf_path: str, config_path: Path | None = None) -> dict[str, Any]:
    """
    A3横のJIS規格PDFから罫線を抽出し、A4 x 2ページのレイアウトデータに変換する。

    Args:
        pdf_path: 参照PDFのファイルパス
        config_path: 抽出パラメータJSONパス（省略時は既定パス）

    Returns:
        レイアウトデータ（v2フォーマット、dict形式）
    """
    config = _load_extraction_config(config_path)

    with fitz.open(pdf_path) as doc:
        page = doc[0]
        segments, page_width, page_height = _extract_raw_segments(page)

    split_x = page_width / 2
    horizontal, vertical = _classify_segments(segments, config)
    left_h, right_h, left_v, right_v = _split_segments_for_pages(
        horizontal, vertical, split_x, config
    )

    page1_lines = _to_reportlab_lines(left_h, left_v, page_height, x_shift=0.0, config=config)
    page2_lines = _to_reportlab_lines(right_h, right_v, page_height, x_shift=split_x, config=config)

    return {
        "source_page_size_pt": [round(page_width, 2), round(page_height, 2)],
        "split_x_pt": round(split_x, 2),
        "page1_lines": page1_lines,
        "page2_lines": page2_lines,
    }


if __name__ == "__main__":
    pdf_path = Path(__file__).parent.parent / "tests/fixtures/R3_pdf_rirekisyo.pdf"
    output_path = (
        Path(__file__).parent.parent / "jtr-generator/assets/data/a4/rirekisho_layout.json"
    )

    data = extract_lines_a3_to_a4x2(str(pdf_path))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✓ Layout data extracted (v2 format)")
    print(f"  page1: {len(data['page1_lines'])} segments")
    print(f"  page2: {len(data['page2_lines'])} segments")
    print(f"  Output: {output_path}")
