from __future__ import annotations

import zipfile
from pathlib import Path

from tools import build_skill_package as bsp


def _write_source_main(base_dir: Path) -> Path:
    source_main = base_dir / "platforms/claude/main.py"
    source_main.parent.mkdir(parents=True, exist_ok=True)
    source_main.write_text(
        '\n'.join(
            [
                "from pathlib import Path",
                'SRC = Path(__file__).parent.parent.parent / \"src\"',
                "base_dir = Path(__file__).parent.parent.parent  # jtr-generator/",
                'schema_path = Path(__file__).parent.parent.parent / "schemas"',
            ]
        ),
        encoding="utf-8",
    )
    return source_main


def test_build_steps_produce_outputs(tmp_path: Path) -> None:
    _write_source_main(tmp_path)

    requirements = bsp.create_requirements(tmp_path)
    assert requirements.exists()
    assert "reportlab" in requirements.read_text(encoding="utf-8")

    patched_main = bsp.modify_paths(tmp_path)
    patched_content = patched_main.read_text(encoding="utf-8")
    assert 'Path(__file__).parent / "src"' in patched_content
    assert 'Path(__file__).parent / "schemas"' in patched_content
    assert "パッケージルート" in patched_content

    sample_file = tmp_path / "build/claude_skill_package/sample.txt"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text("hello", encoding="utf-8")

    zip_path = bsp.create_zip(tmp_path)
    assert zip_path.exists()

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert "sample.txt" in names


def test_main_executes_full_pipeline(tmp_path: Path) -> None:
    _write_source_main(tmp_path)
    package_dir = tmp_path / "build/claude_skill_package"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "placeholder.txt").write_text("keep", encoding="utf-8")

    bsp.main(base_dir=tmp_path)

    assert (tmp_path / "build/claude_skill_package/requirements.txt").exists()
    assert (tmp_path / "build/claude_skill_package/main.py").exists()
    assert (tmp_path / "build/claude.zip").exists()
