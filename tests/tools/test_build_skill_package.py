from __future__ import annotations

import zipfile
from pathlib import Path

from tools import build_skill as bsp


def _write_skill_directory(base_dir: Path) -> Path:
    """skill/ディレクトリに最小限のファイルを作成"""
    skill_dir = base_dir / "skill"
    skill_dir.mkdir(parents=True, exist_ok=True)

    # skill/main.py
    main_py = skill_dir / "main.py"
    main_py.write_text('print("Hello from skill")', encoding="utf-8")

    # skill/SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("# Test Skill", encoding="utf-8")

    return skill_dir


def test_build_steps_produce_outputs(tmp_path: Path) -> None:
    _write_skill_directory(tmp_path)
    build_dir = tmp_path / "build/jtr-generator"

    # copy_skill_directory
    bsp.copy_skill_directory(tmp_path, build_dir)
    assert build_dir.exists()
    assert (build_dir / "main.py").exists()
    assert (build_dir / "SKILL.md").exists()

    # create_requirements
    requirements = bsp.create_requirements(build_dir)
    assert requirements.exists()
    assert "reportlab" in requirements.read_text(encoding="utf-8")

    # create_zip
    zip_path = bsp.create_zip(tmp_path)
    assert zip_path.exists()

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "main.py" in names
        assert "SKILL.md" in names
        assert "requirements.txt" in names


def test_main_executes_full_pipeline(tmp_path: Path) -> None:
    _write_skill_directory(tmp_path)

    bsp.main(base_dir=tmp_path)

    assert (tmp_path / "build/jtr-generator/requirements.txt").exists()
    assert (tmp_path / "build/jtr-generator/main.py").exists()
    assert (tmp_path / "build/jtr-generator.zip").exists()
