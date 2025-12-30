from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path


def _install_layout_metrics_stub(monkeypatch) -> None:
    metrics_module = types.ModuleType("src.layout.metrics")

    def register_font(font_path: Path) -> str:
        return font_path.stem

    def get_font_metrics(_: str, font_size: float) -> dict[str, float]:
        return {"ascent": font_size * 0.8, "descent": -font_size * 0.2, "height": font_size}

    metrics_module.register_font = register_font
    metrics_module.get_font_metrics = get_font_metrics

    # package placeholders
    src_module = types.ModuleType("src")
    layout_module = types.ModuleType("src.layout")

    monkeypatch.setitem(sys.modules, "src", src_module)
    monkeypatch.setitem(sys.modules, "src.layout", layout_module)
    monkeypatch.setitem(sys.modules, "src.layout.metrics", metrics_module)


def _reload_fmr(monkeypatch):
    _install_layout_metrics_stub(monkeypatch)
    if "tools.font_metrics_report" in sys.modules:
        del sys.modules["tools.font_metrics_report"]
    return importlib.import_module("tools.font_metrics_report")


def test_build_report_contains_expected_fields(monkeypatch) -> None:
    fmr = _reload_fmr(monkeypatch)
    font_path = Path("skill/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf")
    report = fmr.build_report(font_path)

    assert report["font"]["name"] == font_path.stem

    name_field = next(field for field in report["centered_fields"] if field["key"] == "name")
    assert name_field["current_baseline"] == 666.0
    assert name_field["expected_baseline"] > 640

    kana_rule = next(rule for rule in report["rule_aligned_fields"] if rule["key"] == "name_kana")
    assert kana_rule["baseline"] == 718.94
    assert kana_rule["metrics"]["ascent"] > 0


def test_main_writes_report(tmp_path, monkeypatch) -> None:
    fmr = _reload_fmr(monkeypatch)
    font_path = Path("skill/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf")
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
