#!/usr/bin/env python3
"""Agent Skillsパッケージをskill/ディレクトリからビルドしてzipを作成"""

import shutil
import zipfile
from pathlib import Path


def _requirements() -> list[str]:
    """pyproject.tomlから requirements.txtを生成"""
    return [
        "reportlab>=4.0.0",
        "pyyaml>=6.0",
        "jsonschema>=4.20.0",
    ]


def create_requirements(build_dir: Path) -> Path:
    """requirements.txtを生成して保存する"""
    print("📋 Creating requirements.txt...")

    requirements = _requirements()
    requirements_path = build_dir / "requirements.txt"
    requirements_path.write_text("\n".join(requirements) + "\n", encoding="utf-8")

    print(f"  + requirements.txt ({len(requirements)} packages)")
    return requirements_path


def copy_skill_directory(base_dir: Path, build_dir: Path) -> None:
    """skill/ディレクトリの内容をビルドディレクトリにコピー"""
    print("📂 Copying skill/ directory...")

    skill_dir = base_dir / "skill"
    if not skill_dir.exists():
        raise FileNotFoundError(f"{skill_dir} not found")

    # skill/の内容をbuild/jtr-generator/にコピー
    if build_dir.exists():
        shutil.rmtree(build_dir)

    shutil.copytree(skill_dir, build_dir)
    print(f"  ✅ Copied {skill_dir} → {build_dir}")


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
    """skill/ディレクトリをコピーして、requirements.txt生成、zip作成を実行"""
    resolved_base = base_dir or Path(__file__).resolve().parent.parent
    build_dir = resolved_base / "build/jtr-generator"

    copy_skill_directory(resolved_base, build_dir)
    create_requirements(build_dir)
    create_zip(resolved_base)


if __name__ == "__main__":
    main()
