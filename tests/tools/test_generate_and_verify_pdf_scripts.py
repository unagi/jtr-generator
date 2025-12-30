from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path

import pypdf


def test_generate_blank_resume_script(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    repo_root = Path(__file__).resolve().parents[2]

    # Stub generate_resume_pdf to write a tiny PDF
    def _stub_generate_resume_pdf(_data, _options, output_path: Path) -> None:
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=100, height=200)
        with open(output_path, "wb") as f:
            writer.write(f)

    dummy_module = types.SimpleNamespace(generate_resume_pdf=_stub_generate_resume_pdf)
    monkeypatch.setitem(sys.modules, "src.generators.pdf", dummy_module)

    runpy.run_path(repo_root / "tools/generate_blank_resume.py", run_name="__main__")

    pdf_path = tmp_path / "outputs/test_resume_lines_only.pdf"
    assert pdf_path.exists()
    reader = pypdf.PdfReader(pdf_path)
    assert len(reader.pages) == 1


def test_verify_pdf_script(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    repo_root = Path(__file__).resolve().parents[2]
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    pdf_path = outputs_dir / "test_resume_lines_only.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=595.0, height=842.0)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    runpy.run_path(repo_root / "tools/verify_pdf.py", run_name="__main__")
