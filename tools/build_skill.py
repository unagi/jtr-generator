#!/usr/bin/env python3
"""Agent Skillsパッケージ用にPythonファイルのパスを修正してzipを作成"""

import re
import zipfile
from collections.abc import Iterable
from pathlib import Path


def _requirements() -> list[str]:
    """pyproject.tomlから requirements.txtを生成"""
    return [
        "reportlab>=4.0.0",
        "pyyaml>=6.0",
        "jsonschema>=4.20.0",
    ]


def create_requirements(base_dir: Path) -> Path:
    """requirements.txtを生成して保存する"""
    print("📋 Creating requirements.txt...")

    requirements = _requirements()
    requirements_path = base_dir / "build/jtr-generator/requirements.txt"
    requirements_path.parent.mkdir(parents=True, exist_ok=True)
    requirements_path.write_text("\n".join(requirements) + "\n", encoding="utf-8")

    print(f"  + requirements.txt ({len(requirements)} packages)")
    return requirements_path


def modify_paths(base_dir: Path) -> Path:
    """パッケージ構造に合わせてパス参照を修正"""
    print("🔧 Modifying Python files for package structure...")

    source_main = base_dir / "main.py"
    target_main = base_dir / "build/jtr-generator/main.py"
    target_main.parent.mkdir(parents=True, exist_ok=True)

    if not source_main.exists():
        raise FileNotFoundError(f"{source_main} not found")

    print(f"  - {source_main.relative_to(base_dir)}")
    main_py = source_main.read_text(encoding="utf-8")

    replacements: Iterable[tuple[str, str]] = [
        (
            r'Path\(__file__\)\.parent\.parent\.parent / "src"',
            r'Path(__file__).parent / "src"',
        ),
        (
            r"base_dir = Path\(__file__\)\.parent\.parent\.parent  # jtr-generator/",
            r"base_dir = Path(__file__).parent  # パッケージルート",
        ),
        (
            r'Path\(__file__\)\.parent\.parent\.parent / "schemas"',
            r'Path(__file__).parent / "schemas"',
        ),
    ]
    for pattern, repl in replacements:
        main_py = re.sub(pattern, repl, main_py)

    target_main.write_text(main_py, encoding="utf-8")

    print("  - src/ files: No modification needed (parent.parent.parent works correctly)")
    print("✅ Python files modified for package structure")
    return target_main


def create_zip(base_dir: Path) -> Path:
    """パッケージディレクトリをzipファイルに圧縮"""
    print("📦 Creating zip archive...")

    package_dir = base_dir / "build/jtr-generator"
    zip_path = base_dir / "build/jtr-generator.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
                print(f"  + {arcname}")

    print(f"✅ Created {zip_path}")
    print(f"   Size: {zip_path.stat().st_size:,} bytes")
    return zip_path


def main(base_dir: Path | None = None) -> None:
    """パス修正、requirements.txt生成、zip作成を実行"""
    resolved_base = base_dir or Path(__file__).resolve().parent.parent
    create_requirements(resolved_base)
    modify_paths(resolved_base)
    create_zip(resolved_base)


if __name__ == "__main__":
    main()
