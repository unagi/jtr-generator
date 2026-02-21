from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reportlab.pdfbase import pdfmetrics
from tools.layout.core_geometry import (
    collect_line_positions,
    expected_baseline,
    nearest_bounds,
    nearest_left,
)

from jtr.layout.metrics import get_font_metrics, register_font

DEFAULT_LAYOUT_PATH = Path("jtr-generator/assets/data/a4/rirekisho_layout.json")
DEFAULT_RULES_PATH = Path("jtr-generator/assets/data/a4/rules/label_alignment.json")
DEFAULT_FONT_PATH = Path("jtr-generator/assets/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf")
DEFAULT_CRITICAL_CELLS_PATH = Path("jtr-generator/assets/data/a4/definitions/manual_bounds.json")
DEFAULT_OUTPUT_PATH = Path("outputs/validation/label_alignment_report.json")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze text alignment/valign using font metrics."
    )
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
        help="Alignment rule JSON.",
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=DEFAULT_FONT_PATH,
        help="Font file path used for metrics.",
    )
    parser.add_argument(
        "--critical-cells",
        type=Path,
        default=DEFAULT_CRITICAL_CELLS_PATH,
        help="Manual bounds JSON for special cells.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1.0,
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


def _resolve_bounds(
    text: dict[str, Any],
    bounds_key: str | None,
    bounds_map: dict[str, dict[str, float]],
    h_lines: list[float],
) -> tuple[float | None, float | None]:
    if bounds_key and bounds_key in bounds_map:
        bounds = bounds_map[bounds_key]
        return bounds["y0"], bounds["y1"]

    y = float(text["y"])
    return nearest_bounds(y, h_lines)


def _build_bounds_map(
    bounds_config: dict[str, Any], critical_cells: dict[str, Any]
) -> dict[str, dict[str, float]]:
    bounds_map: dict[str, dict[str, float]] = {}
    for key, config in bounds_config.items():
        bbox = config.get("bbox_pt")
        if bbox:
            x0, y0, x1, y1 = bbox
            bounds_map[key] = {
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
            }
            continue

        if config.get("source") != "critical_cells":
            continue
        name = config.get("name")
        if not name:
            continue

        for page_cells in critical_cells.values():
            for cell in page_cells:
                if cell.get("name") != name:
                    continue
                x0, y0, x1, y1 = cell["bbox_pt"]
                bounds_map[key] = {
                    "x0": float(x0),
                    "y0": float(y0),
                    "x1": float(x1),
                    "y1": float(y1),
                }
    return bounds_map


def _build_label_rule_index(rules: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for rule in rules.get("labels", []):
        text = rule.get("text")
        if isinstance(text, str) and text not in lookup:
            lookup[text] = rule
    return lookup


def _analyze_text_entry(
    text: dict[str, Any],
    rule: dict[str, Any],
    defaults: dict[str, Any],
    bounds_map: dict[str, dict[str, float]],
    h_lines: list[float],
    v_lines: list[float],
    font_name: str,
    tolerance: float,
) -> dict[str, Any]:
    align = rule.get("align", defaults.get("align", "left"))
    valign = rule.get("valign", defaults.get("valign", "baseline"))
    entry_tolerance = float(rule.get("allow_delta_pt", tolerance))
    manual = bool(rule.get("manual", False))
    bounds_key = rule.get("bounds")

    bottom, top = _resolve_bounds(text, bounds_key, bounds_map, h_lines)
    metrics = get_font_metrics(font_name, float(text["font_size"]))
    text_y = float(text["y"])

    expected_y = None
    status = "baseline"
    margin_top = None
    margin_bottom = None

    if bottom is not None and top is not None and valign in {"center", "top", "bottom"}:
        expected_y = expected_baseline(valign, bottom, top, metrics)
        if valign == "center":
            if expected_y is not None and abs(text_y - expected_y) <= entry_tolerance:
                status = "ok"
            else:
                status = "needs_review"
        else:
            status = "needs_margin"
            if valign == "top":
                margin_top = top - (text_y + metrics["ascent"])
            else:
                margin_bottom = (text_y + metrics["descent"]) - bottom

    if valign == "baseline":
        status = "baseline"
    if manual:
        status = "manual"

    left_ref = nearest_left(float(text["x"]), v_lines)
    left_margin = None if left_ref is None else float(text["x"]) - left_ref
    delta = None if expected_y is None else text_y - expected_y

    return {
        "text": text["text"],
        "x": text["x"],
        "y": text["y"],
        "font_size": text["font_size"],
        "align": align,
        "valign": valign,
        "status": status,
        "bounds": {
            "bottom": bottom,
            "top": top,
            "source": bounds_key or "nearest_lines",
        },
        "expected_y": expected_y,
        "delta": delta,
        "metrics": metrics,
        "tolerance_pt": entry_tolerance,
        "margins": {
            "left": left_margin,
            "top": margin_top,
            "bottom": margin_bottom,
        },
    }


def _analyze_pages(
    layout: dict[str, Any],
    rules: dict[str, Any],
    bounds_map: dict[str, dict[str, float]],
    font_name: str,
    tolerance: float,
) -> dict[str, list[dict[str, Any]]]:
    defaults = rules.get("defaults", {})
    rule_index = _build_label_rule_index(rules)
    page_reports: dict[str, list[dict[str, Any]]] = {}

    for page_key, line_key, text_key in [
        ("page1", "page1_lines", "page1_texts"),
        ("page2", "page2_lines", "page2_texts"),
    ]:
        texts = layout.get(text_key, [])
        lines = layout.get(line_key, [])
        if not texts or not lines:
            continue

        h_lines = collect_line_positions(lines, axis="y")
        v_lines = collect_line_positions(lines, axis="x")

        page_entries: list[dict[str, Any]] = []
        for text in texts:
            rule = rule_index.get(text.get("text", ""), {})
            page_entries.append(
                _analyze_text_entry(
                    text=text,
                    rule=rule,
                    defaults=defaults,
                    bounds_map=bounds_map,
                    h_lines=h_lines,
                    v_lines=v_lines,
                    font_name=font_name,
                    tolerance=tolerance,
                )
            )
        page_reports[page_key] = page_entries

    return page_reports


def _manual_rules_by_bounds(
    rule_labels: list[dict[str, Any]], fallback_bounds_key: str | None = None
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for rule in rule_labels:
        if not rule.get("manual"):
            continue
        bounds_key = rule.get("bounds")
        if not isinstance(bounds_key, str):
            if fallback_bounds_key is None:
                continue
            bounds_key = fallback_bounds_key
        if not bounds_key:
            continue
        grouped.setdefault(bounds_key, []).append(rule)
    return grouped


def _select_block_texts(
    block_config: dict[str, Any],
    block_rules: list[dict[str, Any]],
    text_lookup: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    lines = block_config.get("block", {}).get("lines")
    if isinstance(lines, list):
        return [text_lookup[text] for text in lines if text in text_lookup]

    fallback_rules = [
        rule
        for rule in block_rules
        if rule.get("align") == "left" and rule.get("valign") == "bottom"
    ]
    return [text_lookup[rule["text"]] for rule in fallback_rules if rule.get("text") in text_lookup]


def _select_title_text(
    block_config: dict[str, Any],
    block_rules: list[dict[str, Any]],
    text_lookup: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    configured_title = block_config.get("title", {}).get("text")
    if isinstance(configured_title, str) and configured_title in text_lookup:
        return text_lookup[configured_title]

    fallback_rules = [
        rule
        for rule in block_rules
        if rule.get("align") == "center" and rule.get("valign") == "center"
    ]
    for rule in fallback_rules:
        text = rule.get("text")
        if isinstance(text, str) and text in text_lookup:
            return text_lookup[text]
    return None


def _analyze_manual_block(
    bounds: dict[str, float],
    block_config: dict[str, Any],
    block_rules: list[dict[str, Any]],
    text_lookup: dict[str, dict[str, Any]],
    font_name: str,
) -> dict[str, Any]:
    manual_block: dict[str, Any] = {
        "bounds": bounds,
        "block": {},
        "title": {},
    }

    block_texts = _select_block_texts(block_config, block_rules, text_lookup)
    if block_texts:
        block_texts_sorted = sorted(block_texts, key=lambda item: item["y"])
        baselines = [float(item["y"]) for item in block_texts_sorted]
        line_gaps = [b - a for a, b in zip(baselines, baselines[1:], strict=False)]
        line_height = sum(line_gaps) / len(line_gaps) if line_gaps else 0.0
        font_size = float(block_texts_sorted[0]["font_size"])
        metrics = get_font_metrics(font_name, font_size)

        baseline_min = baselines[0]
        baseline_max = baselines[-1]
        text_top = baseline_max + metrics["ascent"]
        text_bottom = baseline_min + metrics["descent"]
        left_margin = min(float(item["x"]) for item in block_texts_sorted) - bounds["x0"]

        manual_block["block"] = {
            "lines": [item["text"] for item in block_texts_sorted],
            "font_size": font_size,
            "line_height": round(line_height, 3),
            "baseline_min": baseline_min,
            "baseline_max": baseline_max,
            "text_top": round(text_top, 3),
            "text_bottom": round(text_bottom, 3),
            "margin_bottom": round(text_bottom - bounds["y0"], 3),
            "margin_top": round(bounds["y1"] - text_top, 3),
            "margin_left": round(left_margin, 3),
            "metrics": metrics,
        }

    title = _select_title_text(block_config, block_rules, text_lookup)
    if title:
        font_size = float(title["font_size"])
        metrics = get_font_metrics(font_name, font_size)
        text_width = float(pdfmetrics.stringWidth(title["text"], font_name, font_size))

        block_top = manual_block["block"].get("text_top", bounds["y0"])
        remaining_center = (bounds["y1"] + block_top) / 2
        expected_baseline = remaining_center - (metrics["ascent"] + metrics["descent"]) / 2

        center_x = (bounds["x0"] + bounds["x1"]) / 2
        expected_center_delta = (float(title["x"]) + text_width / 2) - center_x

        manual_block["title"] = {
            "text": title["text"],
            "font_size": font_size,
            "baseline": title["y"],
            "expected_baseline": round(expected_baseline, 3),
            "delta_baseline": round(float(title["y"]) - expected_baseline, 3),
            "text_width": round(text_width, 3),
            "expected_center_x": round(center_x, 3),
            "delta_center_x": round(expected_center_delta, 3),
            "metrics": metrics,
        }

    return manual_block


def _analyze_manual_blocks(
    layout: dict[str, Any],
    rules: dict[str, Any],
    bounds_map: dict[str, dict[str, float]],
    font_name: str,
) -> dict[str, Any]:
    labels = rules.get("labels", [])
    fallback_bounds_key = "photo_text_area" if "photo_text_area" in bounds_map else None
    manual_rules = _manual_rules_by_bounds(labels, fallback_bounds_key)
    manual_block_rules = rules.get("manual_blocks", {})

    if not manual_rules:
        return {}

    if not isinstance(manual_block_rules, dict):
        manual_block_rules = {}

    result: dict[str, Any] = {}
    target_keys = set(manual_rules)
    target_keys.update(manual_block_rules.keys())

    for block_key in sorted(target_keys):
        bounds = bounds_map.get(block_key)
        if not bounds:
            continue

        config = manual_block_rules.get(block_key, {})
        if not isinstance(config, dict):
            config = {}
        page_key = str(config.get("page", "page1"))
        texts = layout.get(f"{page_key}_texts", [])
        text_lookup = {text["text"]: text for text in texts}

        result[block_key] = _analyze_manual_block(
            bounds=bounds,
            block_config=config,
            block_rules=manual_rules.get(block_key, []),
            text_lookup=text_lookup,
            font_name=font_name,
        )

    return result


def main() -> None:
    args = _parse_args()

    layout = _load_json(args.layout)
    rules = _load_json(args.rules)
    critical_cells = _load_json(args.critical_cells) if args.critical_cells.exists() else {}

    font_name = register_font(args.font)
    bounds_map = _build_bounds_map(rules.get("bounds", {}), critical_cells)

    report: dict[str, Any] = {
        "layout": str(args.layout),
        "rules": str(args.rules),
        "font": str(args.font),
        "tolerance_pt": args.tolerance,
        "pages": _analyze_pages(
            layout=layout,
            rules=rules,
            bounds_map=bounds_map,
            font_name=font_name,
            tolerance=args.tolerance,
        ),
    }

    manual_blocks = _analyze_manual_blocks(
        layout=layout,
        rules=rules,
        bounds_map=bounds_map,
        font_name=font_name,
    )
    if manual_blocks:
        report["manual_blocks"] = manual_blocks

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
