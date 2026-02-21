from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.layout.core_geometry import (
    collect_line_positions,
    expected_baseline,
    nearest_bounds,
    nearest_left,
)

from jtr.layout.metrics import get_font_metrics, register_font

DEFAULT_LAYOUT_PATH = Path("jtr-generator/assets/data/a4/rirekisho_layout.json")
DEFAULT_RULES_PATH = Path("jtr-generator/assets/data/a4/rules/field_alignment.json")
DEFAULT_FONT_PATH = Path("jtr-generator/assets/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf")
DEFAULT_OUTPUT_PATH = Path("outputs/validation/field_alignment_report.json")
LEGACY_STACKED_BLOCK_KEYS = {"phone_block", "contact_phone_block"}


@dataclass(frozen=True)
class StackedSeed:
    expected_first: float | None
    line_height: float


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze data field alignment using font metrics.")
    parser.add_argument(
        "--layout",
        type=Path,
        default=DEFAULT_LAYOUT_PATH,
        help="Layout JSON with absolute positions.",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=DEFAULT_RULES_PATH,
        help="Data field alignment rule JSON.",
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=DEFAULT_FONT_PATH,
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
        default=DEFAULT_OUTPUT_PATH,
        help="Output report JSON path.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _alignment_status(valign: str, delta: float | None, tolerance: float) -> str:
    if valign == "baseline":
        return "baseline"
    if delta is None:
        return "ok"
    return "needs_review" if abs(delta) > tolerance else "ok"


def _compute_margin_left(x: float, v_lines: list[float]) -> float | None:
    left_ref = nearest_left(x, v_lines)
    return None if left_ref is None else x - left_ref


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
    bottom, top = nearest_bounds(y, h_lines)
    metrics = get_font_metrics(font_name, float(field["font_size"]))

    expected_y = expected_baseline(valign, bottom, top, metrics, margin_top, margin_bottom)
    delta = None if expected_y is None else y - expected_y

    status = _alignment_status(valign, delta, tolerance)
    computed_margin_left = _compute_margin_left(float(field["x"]), v_lines)

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


def _build_stacked_seed(
    first: dict[str, Any], block_rule: dict[str, Any], h_lines: list[float], font_name: str
) -> StackedSeed:
    top = nearest_bounds(float(first["y"]), h_lines)[1]
    metrics = get_font_metrics(font_name, float(first["font_size"]))
    margin_top = float(block_rule.get("margin_top", 0.0))
    expected_first = None if top is None else top - metrics["ascent"] - margin_top
    return StackedSeed(
        expected_first=expected_first, line_height=float(block_rule.get("line_height", 0.0))
    )


def _stacked_expected_y(seed: StackedSeed, idx: int) -> float | None:
    if seed.expected_first is None or seed.line_height == 0:
        return None
    return seed.expected_first - (seed.line_height * idx)


def _analyze_stacked_entry(
    field_key: str,
    field: dict[str, Any],
    idx: int,
    seed: StackedSeed,
    v_lines: list[float],
    tolerance: float,
) -> dict[str, Any]:
    expected_y = _stacked_expected_y(seed, idx)
    delta = None if expected_y is None else float(field["y"]) - expected_y
    status = _alignment_status("top", delta, tolerance)
    computed_margin_left = _compute_margin_left(float(field["x"]), v_lines)

    return {
        "field": field_key,
        "x": field["x"],
        "y": field["y"],
        "expected_y": expected_y,
        "delta": delta,
        "status": status,
        "computed_margin_left": computed_margin_left,
    }


def _iter_existing_fields(
    field_keys: list[str], layout_fields: dict[str, Any]
) -> list[tuple[int, str, dict[str, Any]]]:
    return [
        (idx, key, field)
        for idx, key in enumerate(field_keys)
        if (field := layout_fields.get(key)) is not None
    ]


def _analyze_stacked_block(
    block_rule: dict[str, Any],
    layout_fields: dict[str, Any],
    h_lines: list[float],
    v_lines: list[float],
    font_name: str,
    tolerance: float,
) -> dict[str, Any]:
    fields = block_rule.get("fields", [])
    if not fields:
        return {"status": "missing_fields"}

    first_key = fields[0]
    first = layout_fields.get(first_key)
    if not first:
        return {"status": "missing_first"}

    seed = _build_stacked_seed(first, block_rule, h_lines, font_name)
    entries = [
        _analyze_stacked_entry(key, field, idx, seed, v_lines, tolerance)
        for idx, key, field in _iter_existing_fields(fields, layout_fields)
    ]

    return {
        "align": block_rule.get("align"),
        "valign": block_rule.get("valign"),
        "line_height": seed.line_height,
        "margin_left": block_rule.get("margin_left"),
        "margin_top": block_rule.get("margin_top"),
        "fields": entries,
    }


def _analyze_multiline_entry(
    key: str,
    block_rule: dict[str, Any],
    field: dict[str, Any],
    page2_h: list[float],
    font_name: str,
    tolerance: float,
) -> dict[str, Any]:
    y_top = float(field["y_top"])
    bottom, top = nearest_bounds(y_top, page2_h)
    metrics = get_font_metrics(font_name, float(field["font_size"]))
    expected_y = expected_baseline(
        block_rule.get("valign", "top"),
        bottom,
        top,
        metrics,
        block_rule.get("margin_top"),
        block_rule.get("margin_bottom"),
    )
    delta = None if expected_y is None else y_top - expected_y
    status = _alignment_status(block_rule.get("valign", "top"), delta, tolerance)
    return {
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


def _analyze_page1_fields(
    page1_fields: dict[str, Any],
    page1_rules: dict[str, Any],
    page1_h: list[float],
    page1_v: list[float],
    font_name: str,
    tolerance: float,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    for key, field in page1_fields.items():
        if field.get("type"):
            continue
        entries.append(
            _analyze_single_field(key, field, page1_rules, page1_h, page1_v, font_name, tolerance)
        )

    stacked_blocks: dict[str, dict[str, Any]] = {}
    for block_key, block_rule in page1_rules.items():
        if not isinstance(block_rule, dict) or not _is_stacked_block_rule(block_key, block_rule):
            continue
        stacked_blocks[block_key] = _analyze_stacked_block(
            block_rule, page1_fields, page1_h, page1_v, font_name, tolerance
        )

    return entries, stacked_blocks


def _analyze_multiline_blocks(
    page2_rules: dict[str, Any],
    page2_fields: dict[str, Any],
    page2_h: list[float],
    font_name: str,
    tolerance: float,
) -> list[dict[str, Any]]:
    multiline_entries: list[dict[str, Any]] = []
    for key, block_rule in page2_rules.items():
        field = page2_fields.get(key)
        if not field:
            multiline_entries.append({"field": key, "status": "missing_field"})
            continue
        multiline_entries.append(
            _analyze_multiline_entry(key, block_rule, field, page2_h, font_name, tolerance)
        )
    return multiline_entries


def _is_stacked_block_rule(rule_key: str, rule: dict[str, Any]) -> bool:
    fields = rule.get("fields")
    if not isinstance(fields, list):
        return False
    if rule.get("type") == "stacked_lines":
        return True
    return rule_key in LEGACY_STACKED_BLOCK_KEYS


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

    page1_fields = layout.get("page1_data_fields", {})
    page1_rules = rules.get("page1_fields", {})
    page1_lines = layout.get("page1_lines", [])
    page1_h = collect_line_positions(page1_lines, axis="y")
    page1_v = collect_line_positions(page1_lines, axis="x")
    page1_entries, stacked_blocks = _analyze_page1_fields(
        page1_fields, page1_rules, page1_h, page1_v, font_name, tolerance
    )
    report["pages"]["page1"] = page1_entries
    report.update(stacked_blocks)

    page2_fields = layout.get("page2_data_fields", {})
    page2_rules = rules.get("multiline_blocks", {})
    page2_lines = layout.get("page2_lines", [])
    page2_h = collect_line_positions(page2_lines, axis="y")
    report["multiline_blocks"] = _analyze_multiline_blocks(
        page2_rules, page2_fields, page2_h, font_name, tolerance
    )

    report["dynamic_rows"] = rules.get("dynamic_rows", {})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
