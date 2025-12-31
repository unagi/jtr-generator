import argparse
import json
from pathlib import Path
from typing import Any

from reportlab.pdfbase import pdfmetrics

from skill.scripts.jtr.layout.metrics import get_font_metrics, register_font


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze text alignment/valign using font metrics."
    )
    parser.add_argument(
        "--layout",
        type=Path,
        default=Path("skill/assets/data/a4/rirekisho_layout.json"),
        help="Layout JSON with absolute positions.",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path("skill/assets/data/a4/rules/label_alignment.json"),
        help="Alignment rule JSON.",
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=Path("skill/assets/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf"),
        help="Font file path used for metrics.",
    )
    parser.add_argument(
        "--critical-cells",
        type=Path,
        default=Path("skill/assets/data/a4/definitions/manual_bounds.json"),
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
        default=Path("outputs/validation/label_alignment_report.json"),
        help="Output report JSON path.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _nearest_bounds(value: float, positions: list[float]) -> tuple[float | None, float | None]:
    below = [pos for pos in positions if pos <= value]
    above = [pos for pos in positions if pos >= value]
    return (max(below) if below else None, min(above) if above else None)


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
    return _nearest_bounds(y, h_lines)


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
                if cell.get("name") == name:
                    x0, y0, x1, y1 = cell["bbox_pt"]
                    bounds_map[key] = {
                        "x0": float(x0),
                        "y0": float(y0),
                        "x1": float(x1),
                        "y1": float(y1),
                    }
    return bounds_map


def _text_rule_lookup(text: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    for rule in rules.get("labels", []):
        if rule.get("text") == text.get("text"):
            return rule
    return {}


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
        "pages": {},
    }

    defaults = rules.get("defaults", {})
    rule_labels = rules.get("labels", [])

    for page_key, line_key, text_key in [
        ("page1", "page1_lines", "page1_texts"),
        ("page2", "page2_lines", "page2_texts"),
    ]:
        texts = layout.get(text_key, [])
        lines = layout.get(line_key, [])
        if not texts or not lines:
            continue

        h_lines = _collect_line_positions(lines, axis="y")
        v_lines = _collect_line_positions(lines, axis="x")

        page_entries: list[dict[str, Any]] = []
        for text in texts:
            rule = _text_rule_lookup(text, rules)
            align = rule.get("align", defaults.get("align", "left"))
            valign = rule.get("valign", defaults.get("valign", "baseline"))
            entry_tolerance = float(rule.get("allow_delta_pt", args.tolerance))
            manual = bool(rule.get("manual", False))
            bounds_key = rule.get("bounds")

            bottom, top = _resolve_bounds(text, bounds_key, bounds_map, h_lines)
            metrics = get_font_metrics(font_name, float(text["font_size"]))

            expected_y = None
            status = "baseline"
            margin_top = None
            margin_bottom = None

            if bottom is not None and top is not None:
                center = bottom + (top - bottom) / 2

                if valign == "center":
                    expected_y = center - (metrics["ascent"] + metrics["descent"]) / 2
                    status = (
                        "ok" if abs(text["y"] - expected_y) <= entry_tolerance else "needs_review"
                    )
                elif valign == "top":
                    expected_y = top - metrics["ascent"]
                    status = "needs_margin"
                    margin_top = top - (float(text["y"]) + metrics["ascent"])
                elif valign == "bottom":
                    expected_y = bottom - metrics["descent"]
                    status = "needs_margin"
                    margin_bottom = (float(text["y"]) + metrics["descent"]) - bottom

            if valign == "baseline":
                status = "baseline"

            if manual:
                status = "manual"

            left_margin = None
            if align == "left" and v_lines:
                left_lines = [x for x in v_lines if x <= float(text["x"])]
                if left_lines:
                    left = max(left_lines)
                    left_margin = float(text["x"]) - left

            delta = None
            if expected_y is not None:
                delta = float(text["y"]) - expected_y

            entry = {
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
            page_entries.append(entry)

        report["pages"][page_key] = page_entries

    manual_rules = [rule for rule in rule_labels if rule.get("manual")]
    manual_bounds_key = "photo_text_area"
    if manual_rules and manual_bounds_key in bounds_map:
        photo_bounds = bounds_map[manual_bounds_key]
        page1_texts = layout.get("page1_texts", [])
        text_lookup = {text["text"]: text for text in page1_texts}

        title_rules = [
            rule
            for rule in manual_rules
            if rule.get("align") == "center" and rule.get("valign") == "center"
        ]
        block_rules = [
            rule
            for rule in manual_rules
            if rule.get("align") == "left" and rule.get("valign") == "bottom"
        ]

        block_texts = [
            text_lookup[rule["text"]] for rule in block_rules if rule.get("text") in text_lookup
        ]
        title_texts = [
            text_lookup[rule["text"]] for rule in title_rules if rule.get("text") in text_lookup
        ]

        manual_block = {
            "bounds": photo_bounds,
            "block": {},
            "title": {},
        }

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

            left_margin = min(float(item["x"]) for item in block_texts_sorted) - photo_bounds["x0"]

            manual_block["block"] = {
                "lines": [item["text"] for item in block_texts_sorted],
                "font_size": font_size,
                "line_height": round(line_height, 3),
                "baseline_min": baseline_min,
                "baseline_max": baseline_max,
                "text_top": round(text_top, 3),
                "text_bottom": round(text_bottom, 3),
                "margin_bottom": round(text_bottom - photo_bounds["y0"], 3),
                "margin_top": round(photo_bounds["y1"] - text_top, 3),
                "margin_left": round(left_margin, 3),
                "metrics": metrics,
            }

        if title_texts:
            title = title_texts[0]
            font_size = float(title["font_size"])
            metrics = get_font_metrics(font_name, font_size)
            text_width = float(pdfmetrics.stringWidth(title["text"], font_name, font_size))

            block_top = manual_block["block"].get("text_top", photo_bounds["y0"])
            remaining_center = (photo_bounds["y1"] + block_top) / 2
            expected_baseline = remaining_center - (metrics["ascent"] + metrics["descent"]) / 2

            center_x = (photo_bounds["x0"] + photo_bounds["x1"]) / 2
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

        report["manual_blocks"] = {
            manual_bounds_key: manual_block,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
