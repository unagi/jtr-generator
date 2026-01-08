"""pytest共通設定・フィクスチャ定義"""

import sys
from pathlib import Path

import pytest

# jtr-generator/scripts/ をモジュールパスに追加
_repo_root = Path(__file__).parent.parent
_scripts_dir = _repo_root / "jtr-generator" / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


@pytest.fixture
def fixtures_dir() -> Path:
    """テストフィクスチャのルートディレクトリを返す"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures_dir(fixtures_dir: Path) -> Path:
    """正常系フィクスチャディレクトリを返す"""
    return fixtures_dir / "valid"


@pytest.fixture
def invalid_fixtures_dir(fixtures_dir: Path) -> Path:
    """異常系フィクスチャディレクトリを返す"""
    return fixtures_dir / "invalid"


@pytest.fixture
def schema_path() -> Path:
    """JSON Schemaファイルのパスを返す"""
    return Path(__file__).parent.parent / "jtr-generator" / "assets" / "schemas" / "rirekisho_schema.json"
