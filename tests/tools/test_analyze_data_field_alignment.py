from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.layout import analyze_data_field_alignment as adfa


def _stub_metrics() -> dict[str, float]:
    return {"ascent": 8.0, "descent": -2.0, "height": 10.0}


def _write_layout(tmp_path: Path) -> Path:
    layout = {
        "page1_lines": [
            {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 0.0, "width": 1.0},
            {"x0": 0.0, "y0": 20.0, "x1": 100.0, "y1": 20.0, "width": 1.0},
            {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 20.0, "width": 1.0},
            {"x0": 50.0, "y0": 0.0, "x1": 50.0, "y1": 20.0, "width": 1.0},
        ],
        "page1_data_fields": {
            "name": {
                "x": 10.0,
                "y": 10.0,
                "font_size": 10.0,
            },
            "phone_line1": {
                "x": 5.0,
                "y": 18.0,
                "font_size": 10.0,
            },
            "phone_line2": {
                "x": 5.0,
                "y": 10.0,
                "font_size": 10.0,
            },
        },
        "page2_lines": [
            {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 0.0, "width": 1.0},
            {"x0": 0.0, "y0": 20.0, "x1": 100.0, "y1": 20.0, "width": 1.0},
        ],
        "page2_data_fields": {
            "history_block": {
                "x_left": 0.0,
                "y_top": 18.0,
                "font_size": 10.0,
            }
        },
    }
    path = tmp_path / "layout.json"
    path.write_text(json.dumps(layout), encoding="utf-8")
    return path


def _write_rules(tmp_path: Path) -> Path:
    rules = {
        "tolerance_pt": 2.0,
        "page1_fields": {
            "name": {
                "align": "left",
                "valign": "center",
                "margin_left": 0.0,
            },
            "phone_block": {
                "fields": ["phone_line1", "phone_line2"],
                "margin_top": 0.5,
                "line_height": 6.0,
            },
            "skip_field": {"type": "manual"},
        },
        "multiline_blocks": {
            "history_block": {
                "align": "left",
                "valign": "top",
                "margin_top": 1.0,
                "margin_bottom": 0.0,
            },
            "missing_block": {"align": "left", "valign": "top"},
        },
        "dynamic_rows": {"education_rows": {"max": 10}},
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules), encoding="utf-8")
    return path


def test_main_generates_report(monkeypatch, tmp_path: Path) -> None:
    layout_path = _write_layout(tmp_path)
    rules_path = _write_rules(tmp_path)
    output_path = tmp_path / "report.json"

    monkeypatch.setattr(adfa, "register_font", lambda _: "stub-font")
    monkeypatch.setattr(adfa, "get_font_metrics", lambda *_args, **_kwargs: _stub_metrics())

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "adfa",
            "--layout",
            str(layout_path),
            "--rules",
            str(rules_path),
            "--font",
            str(tmp_path / "dummy.ttf"),
            "--output",
            str(output_path),
        ],
    )

    adfa.main()

    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "pages" in data
    page1_entries = {entry["field"]: entry for entry in data["pages"]["page1"]}
    assert "name" in page1_entries
    assert data["phone_block"]["fields"][0]["status"] in {"ok", "needs_review"}
    assert data["multiline_blocks"][0]["field"] == "history_block"
    assert any(block["field"] == "missing_block" for block in data["multiline_blocks"])
    assert "education_rows" in data["dynamic_rows"]


def test_custom_stacked_block_is_reported(monkeypatch, tmp_path: Path) -> None:
    layout = {
        "page1_lines": [
            {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 0.0, "width": 1.0},
            {"x0": 0.0, "y0": 20.0, "x1": 100.0, "y1": 20.0, "width": 1.0},
            {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 20.0, "width": 1.0},
        ],
        "page1_data_fields": {
            "custom_line1": {"x": 5.0, "y": 18.0, "font_size": 10.0},
            "custom_line2": {"x": 5.0, "y": 10.0, "font_size": 10.0},
        },
        "page2_lines": [],
        "page2_data_fields": {},
    }
    rules = {
        "tolerance_pt": 2.0,
        "page1_fields": {
            "custom_block": {
                "type": "stacked_lines",
                "fields": ["custom_line1", "custom_line2"],
                "align": "left",
                "valign": "top",
                "margin_top": 0.5,
                "line_height": 6.0,
            }
        },
        "multiline_blocks": {},
        "dynamic_rows": {},
    }
    layout_path = tmp_path / "layout_custom.json"
    rules_path = tmp_path / "rules_custom.json"
    output_path = tmp_path / "report_custom.json"
    layout_path.write_text(json.dumps(layout), encoding="utf-8")
    rules_path.write_text(json.dumps(rules), encoding="utf-8")

    monkeypatch.setattr(adfa, "register_font", lambda _: "stub-font")
    monkeypatch.setattr(adfa, "get_font_metrics", lambda *_args, **_kwargs: _stub_metrics())

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "adfa",
            "--layout",
            str(layout_path),
            "--rules",
            str(rules_path),
            "--font",
            str(tmp_path / "dummy.ttf"),
            "--output",
            str(output_path),
        ],
    )

    adfa.main()

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert "custom_block" in data
    assert data["custom_block"]["fields"][0]["field"] == "custom_line1"
