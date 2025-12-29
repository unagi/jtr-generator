import argparse
import json
from pathlib import Path

from src.layout.anchors import build_text_anchors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build relative text anchors from an existing layout JSON."
    )
    parser.add_argument(
        "--layout",
        type=Path,
        default=Path("data/layouts/resume_layout_a4_v2.json"),
        help="Input layout JSON with absolute positions.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/layouts/resume_layout_a4_v2_text_anchors.json"),
        help="Output anchor JSON path.",
    )
    parser.add_argument(
        "--tol",
        type=float,
        default=0.2,
        help="Clustering tolerance for line positions (pt).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    with open(args.layout, encoding="utf-8") as f:
        layout = json.load(f)

    page1_texts = layout.get("page1_texts", [])
    page2_texts = layout.get("page2_texts", [])

    anchor_data = {
        "format_version": "v1",
        "source_layout": str(args.layout),
        "anchor_strategy": "nearest_line",
        "cluster_tolerance_pt": args.tol,
        "page1_texts": build_text_anchors(page1_texts, layout["page1_lines"], tol=args.tol),
        "page2_texts": build_text_anchors(page2_texts, layout["page2_lines"], tol=args.tol),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(anchor_data, f, ensure_ascii=False, indent=2)

    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
