from __future__ import annotations

import json
from pathlib import Path

import pytest
from jtr.layout import career_sheet


def _write_rules(path: Path) -> None:
    rules = {
        "spacing_mm": {
            "xs": 1.5,
            "sm": 2.0,
            "md": 3.0,
            "lg": 4.0,
            "xl": 6.0,
            "xxl": 8.0,
            "xxxl": 10.0,
        },
        "spacing_pt": {
            "title_after": 5,
            "h1_before": 20,
            "h1_after": 10,
            "h2_before": 10,
            "h2_after": 3,
            "h2_rule_before": 1,
            "h2_rule_after": 3,
            "h3_before": 10,
            "h3_after": 9,
            "h4_before": 8,
            "h4_after": 7,
            "h5_before": 15,
            "h5_after": 5,
            "h6_before": 15,
            "h6_after": 3,
            "h7_before": 15,
            "h7_after": 1,
            "body_after": 3,
            "heading_bar_padding_x": 8.503937,
            "heading_bar_padding_y": 4.251969,
            "heading_bar_before": 17,
            "heading_bar_after": 6,
            "body_leading": 15,
        },
        "indent_mm": {
            "heading3": 2.0,
            "heading4": 4.0,
            "bullet_left": 8.0,
            "bullet_hanging": 3.0,
        },
    }
    path.write_text(json.dumps(rules), encoding="utf-8")


def test_load_spacing_rules_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    rules_path = tmp_path / "career_sheet_spacing.json"
    _write_rules(rules_path)
    monkeypatch.setattr(career_sheet, "get_assets_path", lambda *parts: rules_path)

    spacing_mm, spacing_pt, indent_mm = career_sheet.load_career_sheet_spacing_rules()

    assert spacing_mm["xs"] == 1.5
    assert spacing_pt["title_after"] == 5
    assert indent_mm["bullet_left"] == 8.0


def test_load_spacing_rules_missing_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(career_sheet, "get_assets_path", lambda *parts: missing)

    with pytest.raises(FileNotFoundError):
        career_sheet.load_career_sheet_spacing_rules()


def test_load_spacing_rules_missing_section(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rules_path = tmp_path / "career_sheet_spacing.json"
    rules_path.write_text(json.dumps({"spacing_mm": {}}), encoding="utf-8")
    monkeypatch.setattr(career_sheet, "get_assets_path", lambda *parts: rules_path)

    with pytest.raises(ValueError):
        career_sheet.load_career_sheet_spacing_rules()
