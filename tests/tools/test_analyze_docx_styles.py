from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("docx")

from tools import analyze_docx_styles


def test_analyze_docx_styles(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    input_path = repo_root / "tests" / "fixtures" / "rirekisho_sample.docx"
    output_path = tmp_path / "outputs" / "docx_report.json"

    exit_code = analyze_docx_styles.main([str(input_path), "--output", str(output_path)])

    assert exit_code == 0
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source"].endswith("rirekisho_sample.docx")
    assert "paragraphs" in payload
    assert "reportlab_styles" in payload
