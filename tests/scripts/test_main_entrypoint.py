from __future__ import annotations

from importlib import reload
from pathlib import Path
from typing import Any

import pytest

from skill.scripts import main as scripts_main


def _minimal_config() -> dict[str, Any]:
    return {"options": {"date_format": "seireki", "paper_size": "A4"}, "fonts": {}}


def test_rirekisho_branch_uses_session_overrides(monkeypatch: Any, tmp_path: Path) -> None:
    module = reload(scripts_main)
    captured: dict[str, Any] = {}

    monkeypatch.setattr(module, "load_config", lambda _path: _minimal_config())
    monkeypatch.setattr(module, "resolve_font_paths", lambda config: config)
    monkeypatch.setattr(module, "validate_and_load_data", lambda input_data: {"source": input_data})

    def fake_generate_rirekisho_pdf(
        data: dict[str, Any], options: dict[str, Any], output_path: Path
    ) -> None:
        captured["data"] = data
        captured["options"] = options
        captured["output_path"] = output_path

    monkeypatch.setattr(module, "generate_rirekisho_pdf", fake_generate_rirekisho_pdf)

    destination = tmp_path / "rirekisho.pdf"
    result = module.main(
        input_data="input.yaml",
        session_options={"date_format": "wareki", "paper_size": "B5"},
        output_path=destination,
        document_type="rirekisho",
    )

    assert result == destination
    assert captured["data"] == {"source": "input.yaml"}
    assert captured["output_path"] == destination
    assert captured["options"]["date_format"] == "wareki"
    assert captured["options"]["paper_size"] == "B5"
    assert captured["options"]["fonts"] == {}


def test_career_sheet_branch_requires_markdown() -> None:
    with pytest.raises(ValueError):
        scripts_main.main(input_data="rirekisho.yaml", document_type="career_sheet")


def test_career_sheet_branch_delegates(monkeypatch: Any, tmp_path: Path) -> None:
    module = reload(scripts_main)
    captured: dict[str, Any] = {}

    monkeypatch.setattr(module, "load_config", lambda _path: _minimal_config())
    monkeypatch.setattr(module, "resolve_font_paths", lambda config: config)
    monkeypatch.setattr(module, "validate_and_load_data", lambda payload: {"payload": payload})

    def fake_generate(
        rirekisho_data: dict[str, Any],
        markdown_text: str,
        options: dict[str, Any],
        output_path: Path,
    ) -> None:
        captured["rirekisho_data"] = rirekisho_data
        captured["markdown_text"] = markdown_text
        captured["options"] = options
        captured["output_path"] = output_path

    monkeypatch.setattr(module, "generate_career_sheet_pdf", fake_generate)

    destination = tmp_path / "career.pdf"
    result = module.main(
        input_data="rirekisho.yaml",
        document_type="career_sheet",
        markdown_content="**Markdown Body**",
        output_path=destination,
        session_options={"paper_size": "B5"},
    )

    assert result == destination
    assert captured["rirekisho_data"] == {"payload": "rirekisho.yaml"}
    assert captured["markdown_text"] == "**Markdown Body**"
    assert captured["options"]["paper_size"] == "B5"
    assert captured["options"]["fonts"] == {}
    assert captured["output_path"] == destination


def test_both_branch_generates_two_pdfs(monkeypatch: Any, tmp_path: Path) -> None:
    module = reload(scripts_main)
    captured: dict[str, Any] = {"rirekisho": [], "career": []}

    monkeypatch.setattr(module, "load_config", lambda _path: _minimal_config())
    monkeypatch.setattr(module, "resolve_font_paths", lambda config: config)
    monkeypatch.setattr(module, "validate_and_load_data", lambda payload: {"payload": payload})

    def fake_generate_rirekisho(
        data: dict[str, Any], options: dict[str, Any], output_path: Path
    ) -> None:
        captured["rirekisho"].append((data, options, output_path))

    def fake_generate_career(
        rirekisho_data: dict[str, Any],
        markdown_text: str,
        options: dict[str, Any],
        output_path: Path,
    ) -> None:
        captured["career"].append((rirekisho_data, markdown_text, options, output_path))

    monkeypatch.setattr(module, "generate_rirekisho_pdf", fake_generate_rirekisho)
    monkeypatch.setattr(module, "generate_career_sheet_pdf", fake_generate_career)
    monkeypatch.setattr(
        module,
        "_build_both_output_paths",
        lambda output_dir: (output_dir / "rirekisho_fixed.pdf", output_dir / "career_fixed.pdf"),
    )

    output_dir = tmp_path / "outputs"
    results = module.main(
        input_data="rirekisho.yaml",
        document_type="both",
        markdown_content="body",
        output_path=output_dir,
    )

    assert results == [output_dir / "rirekisho_fixed.pdf", output_dir / "career_fixed.pdf"]
    assert captured["rirekisho"][0][0] == {"payload": "rirekisho.yaml"}
    assert captured["career"][0][1] == "body"


def test_parse_args_builds_session_options(monkeypatch: Any) -> None:
    module = reload(scripts_main)
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "rirekisho",
            "inputs/rirekisho.yaml",
            "--date-format",
            "wareki",
            "--paper-size",
            "B5",
        ],
    )

    args = module._parse_args()

    assert args.input_file == Path("inputs/rirekisho.yaml")
    assert args.date_format == "wareki"
    assert args.paper_size == "B5"
