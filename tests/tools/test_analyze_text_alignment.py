from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path


def _stub_metrics() -> dict[str, float]:
    return {"ascent": 8.0, "descent": -2.0, "height": 10.0}


def _write_layout(tmp_path: Path) -> Path:
    layout = {
        "page1_lines": [
            {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 0.0, "width": 1.0},
            {"x0": 0.0, "y0": 20.0, "x1": 100.0, "y1": 20.0, "width": 1.0},
            {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 20.0, "width": 1.0},
        ],
        "page2_lines": [
            {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 0.0, "width": 1.0},
            {"x0": 0.0, "y0": 20.0, "x1": 100.0, "y1": 20.0, "width": 1.0},
        ],
        "page1_texts": [
            {"text": "名前", "x": 5.0, "y": 10.0, "font_size": 10.0},
            {"text": "写真注意", "x": 10.0, "y": 15.0, "font_size": 8.0},
            {"text": "写真注釈1", "x": 8.0, "y": 5.0, "font_size": 8.0},
            {"text": "写真注釈2", "x": 8.0, "y": 2.0, "font_size": 8.0},
        ],
        "page2_texts": [{"text": "備考", "x": 5.0, "y": 18.0, "font_size": 10.0}],
    }
    path = tmp_path / "layout.json"
    path.write_text(json.dumps(layout), encoding="utf-8")
    return path


def _write_rules(tmp_path: Path) -> Path:
    rules = {
        "defaults": {"align": "left", "valign": "center"},
        "labels": [
            {"text": "名前", "align": "left", "valign": "center"},
            {
                "text": "写真注意",
                "align": "center",
                "valign": "center",
                "manual": True,
            },
            {
                "text": "写真注釈1",
                "align": "left",
                "valign": "bottom",
                "manual": True,
            },
            {
                "text": "写真注釈2",
                "align": "left",
                "valign": "bottom",
                "manual": True,
            },
            {"text": "備考", "align": "left", "valign": "top"},
        ],
        "bounds": {
            "photo_text_area": {"bbox_pt": [0.0, 0.0, 50.0, 20.0]},
        },
    }
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules), encoding="utf-8")
    return path


def _write_critical(tmp_path: Path) -> Path:
    data = {"page1": [{"name": "photo", "bbox_pt": [0.0, 0.0, 50.0, 20.0]}]}
    path = tmp_path / "critical.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _install_metric_stubs(monkeypatch) -> None:
    metrics_module = types.SimpleNamespace(
        register_font=lambda _path: "stub-font",
        get_font_metrics=lambda *_args, **_kwargs: _stub_metrics(),
    )
    monkeypatch.setitem(sys.modules, "src", types.ModuleType("src"))
    monkeypatch.setitem(sys.modules, "src.layout", types.ModuleType("src.layout"))
    monkeypatch.setitem(sys.modules, "src.layout.metrics", metrics_module)
    monkeypatch.setattr(
        "tools.layout.analyze_text_alignment.register_font",
        metrics_module.register_font,
        raising=False,
    )
    monkeypatch.setattr(
        "tools.layout.analyze_text_alignment.get_font_metrics",
        metrics_module.get_font_metrics,
        raising=False,
    )
    monkeypatch.setattr(
        "tools.layout.analyze_text_alignment.pdfmetrics.stringWidth",
        lambda text, *_: len(text),
        raising=False,
    )


def test_main_outputs_report(monkeypatch, tmp_path: Path) -> None:
    _install_metric_stubs(monkeypatch)
    layout = _write_layout(tmp_path)
    rules = _write_rules(tmp_path)
    critical = _write_critical(tmp_path)
    output = tmp_path / "text_alignment.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analyze_text_alignment",
            "--layout",
            str(layout),
            "--rules",
            str(rules),
            "--critical-cells",
            str(critical),
            "--font",
            str(tmp_path / "dummy.ttf"),
            "--output",
            str(output),
        ],
    )

    module = importlib.import_module("tools.layout.analyze_text_alignment")
    module.main()

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "pages" in data
    assert any(entry["text"] == "名前" for entry in data["pages"]["page1"])
    assert "manual_blocks" in data
