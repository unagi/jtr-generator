from __future__ import annotations

import json
import sys
from pathlib import Path

from tools import font_metrics_report as fmr


def test_build_report_contains_expected_fields() -> None:
    font_path = Path("fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf")
    report = fmr.build_report(font_path)

    assert report["font"]["name"] == font_path.stem

    name_field = next(field for field in report["centered_fields"] if field["key"] == "name")
    assert name_field["current_baseline"] == 666.0
    assert name_field["expected_baseline"] > 640

    kana_rule = next(rule for rule in report["rule_aligned_fields"] if rule["key"] == "name_kana")
    assert kana_rule["baseline"] == 718.94
    assert kana_rule["metrics"]["ascent"] > 0


def test_main_writes_report(tmp_path, monkeypatch) -> None:
    font_path = Path("fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf")
    output = tmp_path / "report.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "font_metrics_report",
            "--font",
            str(font_path),
            "--output",
            str(output),
        ],
    )

    fmr.main()

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["font"]["name"] == font_path.stem
