#!/usr/bin/env python3
"""Claude Agent Skillsパッケージ用にPythonファイルのパスを修正してzipを作成"""

import re
import zipfile
from pathlib import Path


def create_requirements() -> None:
    """pyproject.tomlから requirements.txtを生成"""
    print("📋 Creating requirements.txt...")

    # pyproject.tomlから依存関係を抽出
    requirements = [
        "reportlab>=4.0.0",
        "pyyaml>=6.0",
        "jsonschema>=4.20.0",
    ]

    requirements_path = Path("build/claude_skill_package/requirements.txt")
    requirements_path.write_text("\n".join(requirements) + "\n", encoding="utf-8")

    print(f"  + requirements.txt ({len(requirements)} packages)")


def modify_paths() -> None:
    """パッケージ構造に合わせてパス参照を修正"""
    print("🔧 Modifying Python files for package structure...")

    # main.pyの修正のみ実施
    # main.pyはパッケージルート直下なので parent.parent.parent → parent に変更
    print("  - platforms/claude/main.py")
    main_py = Path("platforms/claude/main.py").read_text(encoding="utf-8")

    # Line 12: srcインポート用パス
    main_py = re.sub(
        r'Path\(__file__\)\.parent\.parent\.parent / "src"',
        r'Path(__file__).parent / "src"',
        main_py,
    )

    # Line 53: base_dir（フォントパス解決用）
    main_py = re.sub(
        r"base_dir = Path\(__file__\)\.parent\.parent\.parent  # jtr-generator/",
        r"base_dir = Path(__file__).parent  # パッケージルート",
        main_py,
    )

    # Line 179: schema_path
    main_py = re.sub(
        r'Path\(__file__\)\.parent\.parent\.parent / "schemas"',
        r'Path(__file__).parent / "schemas"',
        main_py,
    )

    Path("build/claude_skill_package/main.py").write_text(main_py, encoding="utf-8")

    # src/配下のファイルはパス修正不要
    # src/validators/data.pyやsrc/generators/pdf.pyは parent.parent.parent のままで
    # パッケージ構造でも正しく動作する
    #
    # 理由:
    # src/validators/data.py から見て:
    #   - parent = src/validators/
    #   - parent.parent = src/
    #   - parent.parent.parent = パッケージルート/ ← 正しい！

    print("  - src/ files: No modification needed (parent.parent.parent works correctly)")
    print("✅ Python files modified for package structure")


def create_zip() -> None:
    """パッケージディレクトリをzipファイルに圧縮"""
    print("📦 Creating zip archive...")

    package_dir = Path("build/claude_skill_package")
    zip_path = Path("build/claude.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
                print(f"  + {arcname}")

    print(f"✅ Created {zip_path}")
    print(f"   Size: {zip_path.stat().st_size:,} bytes")


def main() -> None:
    """パス修正、requirements.txt生成、zip作成を実行"""
    create_requirements()
    modify_paths()
    create_zip()


if __name__ == "__main__":
    main()
