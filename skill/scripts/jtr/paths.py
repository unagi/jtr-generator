"""パス解決の共通化モジュール

skill/ ディレクトリとassets/配下のパスを一元管理します。
"""

from pathlib import Path


def get_skill_root() -> Path:
    """skill/ ディレクトリのルートパスを取得

    Returns:
        skill/ ディレクトリの絶対パス

    Note:
        このファイルは skill/scripts/jtr/paths.py に配置されているため、
        parents[2] で skill/ ディレクトリを取得します：
        - parents[0]: skill/scripts/jtr/
        - parents[1]: skill/scripts/
        - parents[2]: skill/
    """
    return Path(__file__).resolve().parents[2]


def get_assets_path(*parts: str) -> Path:
    """assets/配下のパスを取得

    Args:
        *parts: assets/ からの相対パス（複数指定可）

    Returns:
        skill/assets/ 配下の絶対パス

    Examples:
        >>> get_assets_path("config.yaml")
        PosixPath('/path/to/skill/assets/config.yaml')
        >>> get_assets_path("fonts", "BIZ_UDMincho", "BIZUDMincho-Regular.ttf")
        PosixPath('/path/to/skill/assets/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf')
    """
    return get_skill_root() / "assets" / Path(*parts)


def get_schema_path(schema_name: str) -> Path:
    """スキーマファイルのパスを取得

    Args:
        schema_name: スキーマファイル名（例: "resume_schema.json"）

    Returns:
        skill/assets/schemas/ 配下の絶対パス

    Examples:
        >>> get_schema_path("resume_schema.json")
        PosixPath('/path/to/skill/assets/schemas/resume_schema.json')
    """
    return get_assets_path("schemas", schema_name)


def get_layout_path(*parts: str) -> Path:
    """レイアウトデータのパスを取得

    Args:
        *parts: data/ からの相対パス（複数指定可）

    Returns:
        skill/assets/data/ 配下の絶対パス

    Examples:
        >>> get_layout_path("a4", "resume_layout.json")
        PosixPath('/path/to/skill/assets/data/a4/resume_layout.json')
    """
    return get_assets_path("data", *parts)
