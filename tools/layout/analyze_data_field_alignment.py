import argparse
import json
from pathlib import Path
from typing import Any

from jtr.layout.metrics import get_font_metrics, register_font


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze data field alignment using font metrics.")
    parser.add_argument(
        "--layout",
        type=Path,
        default=Path("skill/assets/data/a4/rirekisho_layout.json"),
        help="Layout JSON with absolute positions.",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("skill/assets/data/a4/rules/field_alignment.json"),
        help="Data field alignment rule JSON.",
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=Path("skill/assets/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf"),
        help="Font file path used for metrics.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1.5,
        help="Tolerance for center alignment in pt.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/validation/field_alignment_report.json"),
        help="Output report JSON path.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _collect_line_positions(lines: list[dict[str, Any]], axis: str) -> list[float]:
    positions: list[float] = []
    for line in lines:
        if axis == "x":
            if abs(line["x0"] - line["x1"]) <= 0.01:
                positions.append(float(line["x0"]))
        elif axis == "y":
            if abs(line["y0"] - line["y1"]) <= 0.01:
                positions.append(float(line["y0"]))
    return sorted({round(pos, 3) for pos in positions})


def _nearest_bounds(value: float, positions: list[float]) -> tuple[float | None, float | None]:
    below = [pos for pos in positions if pos <= value]
    above = [pos for pos in positions if pos >= value]
    return (max(below) if below else None, min(above) if above else None)


def _nearest_left(value: float, positions: list[float]) -> float | None:
    lefts = [pos for pos in positions if pos <= value]
    return max(lefts) if lefts else None


def _expected_baseline(
    valign: str,
    bottom: float | None,
    top: float | None,
    metrics: dict[str, float],
    margin_top: float | None,
    margin_bottom: float | None,
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


def _analyze_single_field(
    field_key: str,
    field: dict[str, Any],
    rules: dict[str, Any],
    h_lines: list[float],
    v_lines: list[float],
    font_name: str,
    tolerance: float,
) -> dict[str, Any]:
    rule = rules.get(field_key)
    if not rule:
        return {"field": field_key, "status": "missing_rule"}

    align = rule.get("align", "left")
    valign = rule.get("valign", "baseline")
    margin_left = rule.get("margin_left")
    margin_top = rule.get("margin_top")
    margin_bottom = rule.get("margin_bottom")

    y = float(field["y"])
    bottom, top = _nearest_bounds(y, h_lines)
    metrics = get_font_metrics(font_name, float(field["font_size"]))

    expected_y = _expected_baseline(valign, bottom, top, metrics, margin_top, margin_bottom)
    delta = None if expected_y is None else y - expected_y

    status = "baseline" if valign == "baseline" else "ok"
    if expected_y is not None and abs(delta) > tolerance:
        status = "needs_review"

    left_ref = _nearest_left(float(field["x"]), v_lines)
    computed_margin_left = None
    if left_ref is not None:
        computed_margin_left = float(field["x"]) - left_ref

    return {
        "field": field_key,
        "align": align,
        "valign": valign,
        "x": field["x"],
        "y": field["y"],
        "font_size": field["font_size"],
        "bounds": {"bottom": bottom, "top": top},
        "expected_y": expected_y,
        "delta": delta,
        "status": status,
        "margin_left": margin_left,
        "computed_margin_left": computed_margin_left,
        "metrics": metrics,
    }


def _analyze_phone_block(
    block_rule: dict[str, Any],
    layout_fields: dict[str, Any],
    h_lines: list[float],
    v_lines: list[float],
    font_name: str,
    tolerance: float,
) -> dict[str, Any]:
    fields = block_rule.get("fields", [])
    entries = []
    if not fields:
        return {"status": "missing_fields"}

    first_key = fields[0]
    first = layout_fields.get(first_key)
    if not first:
        return {"status": "missing_first"}

    top = _nearest_bounds(float(first["y"]), h_lines)[1]
    metrics = get_font_metrics(font_name, float(first["font_size"]))
    expected_first = None
    if top is not None:
        expected_first = top - metrics["ascent"] - float(block_rule.get("margin_top", 0.0))

    line_height = float(block_rule.get("line_height", 0.0))
    for idx, key in enumerate(fields):
        field = layout_fields.get(key)
        if not field:
            continue
        expected_y = None
        if expected_first is not None and line_height:
            expected_y = expected_first - (line_height * idx)
        delta = None if expected_y is None else float(field["y"]) - expected_y
        status = "ok"
        if expected_y is not None and abs(delta) > tolerance:
            status = "needs_review"

        left_ref = _nearest_left(float(field["x"]), v_lines)
        computed_margin_left = None
        if left_ref is not None:
            computed_margin_left = float(field["x"]) - left_ref

        entries.append(
            {
                "field": key,
                "x": field["x"],
                "y": field["y"],
                "expected_y": expected_y,
                "delta": delta,
                "status": status,
                "computed_margin_left": computed_margin_left,
            }
        )

    return {
        "align": block_rule.get("align"),
        "valign": block_rule.get("valign"),
        "line_height": line_height,
        "margin_left": block_rule.get("margin_left"),
        "margin_top": block_rule.get("margin_top"),
        "fields": entries,
    }


def main() -> None:
    args = _parse_args()

    layout = _load_json(args.layout)
    rules = _load_json(args.rules)

    font_name = register_font(args.font)

    tolerance = float(rules.get("tolerance_pt", args.tolerance))

    report: dict[str, Any] = {
        "layout": str(args.layout),
        "rules": str(args.rules),
        "font": str(args.font),
        "tolerance_pt": tolerance,
        "pages": {},
        "dynamic_rows": {},
        "multiline_blocks": {},
    }

    page1_rules = rules.get("page1_fields", {})
    page1_fields = layout.get("page1_data_fields", {})
    page1_lines = layout.get("page1_lines", [])
    page1_h = _collect_line_positions(page1_lines, axis="y")
    page1_v = _collect_line_positions(page1_lines, axis="x")

    page1_entries = []
    for key, field in page1_fields.items():
        if field.get("type"):
            continue
        entry = _analyze_single_field(
            key, field, page1_rules, page1_h, page1_v, font_name, tolerance
        )
        page1_entries.append(entry)

    for block_key in ("phone_block", "contact_phone_block"):
        phone_block = page1_rules.get(block_key)
        if phone_block:
            report[block_key] = _analyze_phone_block(
                phone_block, page1_fields, page1_h, page1_v, font_name, tolerance
            )

    report["pages"]["page1"] = page1_entries

    page2_rules = rules.get("multiline_blocks", {})
    page2_fields = layout.get("page2_data_fields", {})
    page2_lines = layout.get("page2_lines", [])
    page2_h = _collect_line_positions(page2_lines, axis="y")

    multiline_entries = []
    for key, block_rule in page2_rules.items():
        field = page2_fields.get(key)
        if not field:
            multiline_entries.append({"field": key, "status": "missing_field"})
            continue
        y_top = float(field["y_top"])
        bottom, top = _nearest_bounds(y_top, page2_h)
        metrics = get_font_metrics(font_name, float(field["font_size"]))
        expected_y = _expected_baseline(
            block_rule.get("valign", "top"),
            bottom,
            top,
            metrics,
            block_rule.get("margin_top"),
            block_rule.get("margin_bottom"),
        )
        delta = None if expected_y is None else y_top - expected_y
        status = "ok"
        if expected_y is not None and abs(delta) > tolerance:
            status = "needs_review"
        multiline_entries.append(
            {
                "field": key,
                "align": block_rule.get("align"),
                "valign": block_rule.get("valign"),
                "y_top": y_top,
                "expected_y": expected_y,
                "delta": delta,
                "status": status,
                "margin_left": block_rule.get("margin_left"),
                "margin_top": block_rule.get("margin_top"),
            }
        )

    report["multiline_blocks"] = multiline_entries

    dynamic_rules = rules.get("dynamic_rows", {})
    for key, rule in dynamic_rules.items():
        report["dynamic_rows"][key] = rule

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
