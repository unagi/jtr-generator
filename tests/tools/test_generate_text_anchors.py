from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path


def _write_layout(tmp_path: Path) -> Path:
    layout = {
        "page1_lines": [{"x0": 0.0, "y0": 0.0, "x1": 10.0, "y1": 0.0, "width": 1.0}],
        "page2_lines": [{"x0": 0.0, "y0": 0.0, "x1": 10.0, "y1": 0.0, "width": 1.0}],
        "page1_texts": [{"text": "A", "x": 1.0, "y": 1.0, "font_size": 8.0}],
        "page2_texts": [{"text": "B", "x": 2.0, "y": 2.0, "font_size": 8.0}],
    }
    path = tmp_path / "layout.json"
    path.write_text(json.dumps(layout), encoding="utf-8")
    return path


def test_generate_text_anchors(monkeypatch, tmp_path: Path) -> None:
    layout_path = _write_layout(tmp_path)
    output_path = tmp_path / "anchors.json"

    # Stub build_text_anchors to avoid dependency on layout internals
    stubbed = [{"text": "stub", "line": 0}]
    monkeypatch.setitem(
        sys.modules,
        "src",
        types.ModuleType("src"),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.layout",
        types.ModuleType("src.layout"),
    )
    monkeypatch.setattr(
        "tools.layout.generate_text_anchors.build_text_anchors",
        lambda *_args, **_kwargs: stubbed,
        raising=False,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_text_anchors",
            "--layout",
            str(layout_path),
            "--output",
            str(output_path),
            "--tol",
            "0.5",
        ],
    )

    module = importlib.import_module("tools.layout.generate_text_anchors")
    module.main()

    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["page1_texts"] == stubbed
    assert data["cluster_tolerance_pt"] == 0.5
