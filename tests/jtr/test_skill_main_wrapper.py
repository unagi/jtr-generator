from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from skill import main as skill_main


def test_main_delegates_to_scripts(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_main(
        input_data: str | Path,
        session_options: dict[str, Any] | None = None,
        output_path: Path | str | None = None,
        document_type: str = "resume",
        markdown_content: str | Path | None = None,
        additional_info: str | Path | None = None,
    ) -> Path:
        captured["input_data"] = input_data
        captured["session_options"] = session_options
        captured["output_path"] = output_path
        captured["document_type"] = document_type
        captured["markdown_content"] = markdown_content
        captured["additional_info"] = additional_info
        return Path("output.pdf")

    monkeypatch.setattr(skill_main.scripts_main, "main", fake_main)

    result = skill_main.main(
        input_data="data.yaml",
        session_options={"date_format": "wareki"},
        output_path=Path("rirekisho.pdf"),
        document_type="career_sheet",
        markdown_content="content",
        additional_info="extra",
    )

    assert result == Path("output.pdf")
    assert captured["input_data"] == "data.yaml"
    assert captured["session_options"] == {"date_format": "wareki"}
    assert captured["output_path"] == Path("rirekisho.pdf")
    assert captured["document_type"] == "career_sheet"
    assert captured["markdown_content"] == "content"
    assert captured["additional_info"] == "extra"


def test_parse_args_builds_session_options(monkeypatch: Any) -> None:
    module = importlib.reload(skill_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "inputs/resume.yaml",
            "--date-format",
            "wareki",
            "--paper-size",
            "B5",
        ],
    )

    input_file, options = module._parse_args()

    assert input_file == Path("inputs/resume.yaml")
    assert options == {"date_format": "wareki", "paper_size": "B5"}
