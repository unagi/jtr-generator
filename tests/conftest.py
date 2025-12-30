"""pytest共通設定・フィクスチャ定義"""

from pathlib import Path

import pytest


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
    return Path(__file__).parent.parent / "skill" / "assets" / "schemas" / "resume_schema.json"
