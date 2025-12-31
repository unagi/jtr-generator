from __future__ import annotations

from pathlib import Path

from tools import manual_career_sheet_generation as script


def test_manual_script_main(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    generated = tmp_path / "outputs/test_career_sheet.pdf"

    def _fake_generate(output_path: Path) -> Path:
        output_path.parent.mkdir(exist_ok=True, parents=True)
        output_path.write_bytes(b"%PDF-1.4")
        return output_path

    monkeypatch.setattr(script, "_generate", _fake_generate)

    exit_code = script.main()

    assert exit_code == 0
    assert generated.exists()
