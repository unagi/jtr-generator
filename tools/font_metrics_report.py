"""
フォントメトリクスのサマリを生成するユーティリティ

BIZ UD明朝フォントを前提に、レイアウト調整で参照したい
主要フィールドのベースラインを一か所で確認できるようにします。
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from skill.jtr.layout.metrics import get_font_metrics, register_font


@dataclass(frozen=True)
class FieldBounds:
    key: str
    top: float
    bottom: float
    font_size: float
    description: str
    current_baseline: float | None = None

    def to_report(self, metrics: dict[float, dict[str, float]]) -> dict[str, float | str]:
        font_metrics = metrics[self.font_size]
        center = self.bottom + (self.top - self.bottom) / 2
        expected_baseline = center - (font_metrics["ascent"] + font_metrics["descent"]) / 2
        delta = None
        if self.current_baseline is not None:
            delta = self.current_baseline - expected_baseline

        return {
            "key": self.key,
            "top": self.top,
            "bottom": self.bottom,
            "font_size": self.font_size,
            "description": self.description,
            "expected_baseline": round(expected_baseline, 3),
            "current_baseline": self.current_baseline,
            "delta_from_expected": round(delta, 3) if delta is not None else None,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate consolidated font metric report")
    parser.add_argument(
        "--font",
        type=Path,
        default=Path("skill/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf"),
        help="Path to the font file used for layout calculations.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/debug/font_metrics_report.json"),
        help="Destination for the generated report (JSON).",
    )
    return parser.parse_args()


def _build_metrics(font_name: str, sizes: Iterable[float]) -> dict[float, dict[str, float]]:
    return {size: get_font_metrics(font_name, size) for size in sizes}


def _education_rows() -> list[FieldBounds]:
    row_tops = [740.98, 715.18, 689.38, 663.58, 637.78, 611.98]
    row_bottoms = [716.14, 690.34, 664.54, 638.74, 612.94, 587.10]
    return [
        FieldBounds(
            key=f"education_row_{index}",
            top=top,
            bottom=bottom,
            font_size=11.0,
            description="学歴・職歴行 (11pt)",
        )
        for index, (top, bottom) in enumerate(zip(row_tops, row_bottoms, strict=True), start=1)
    ]


def _report_rule_aligned_fields(
    metrics: dict[float, dict[str, float]],
) -> list[dict[str, float | str]]:
    # ふりがな欄はセル下端罫線にbaselineを合わせる設計
    return [
        {
            "key": "name_kana",
            "font_size": 10.0,
            "baseline": 718.94,
            "description": "ふりがな欄は下端罫線に揃える",
            "metrics": metrics[10.0],
        }
    ]


def build_report(font_path: Path) -> dict[str, object]:
    font_name = register_font(font_path)
    metrics = _build_metrics(font_name, [10.0, 11.0, 28.0])

    centered_fields = [
        FieldBounds(
            key="name",
            top=718.94,
            bottom=633.5,
            font_size=28.0,
            description="氏名欄 (28pt)",
            current_baseline=666.0,
        )
    ]

    centered_fields.extend(_education_rows())

    return {
        "font": {
            "path": str(font_path),
            "name": font_name,
            "metrics": {size: metrics[size] for size in sorted(metrics)},
        },
        "centered_fields": [field.to_report(metrics) for field in centered_fields],
        "rule_aligned_fields": _report_rule_aligned_fields(metrics),
    }


def main() -> None:
    args = _parse_args()
    report = build_report(args.font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Saved: {args.output}")
    print(f"Font: {report['font']['name']} ({report['font']['path']})")
    print(f"Fields analyzed: {len(report['centered_fields']) + len(report['rule_aligned_fields'])}")


if __name__ == "__main__":
    main()
