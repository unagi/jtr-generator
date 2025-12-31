from __future__ import annotations

import zipfile
from pathlib import Path


def test_skill_directory_zips_flat(monkeypatch, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    skill_dir = repo_root / "skill"
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    zip_path = build_dir / "jtr-generator.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_dir.rglob("*"):
            if file_path.is_file() and "__pycache__" not in file_path.parts:
                zf.write(file_path, file_path.relative_to(skill_dir))

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

    assert "SKILL.md" in names
    assert "requirements.txt" in names
    assert "scripts/main.py" in names
    assert any(name.startswith("assets/") for name in names)
