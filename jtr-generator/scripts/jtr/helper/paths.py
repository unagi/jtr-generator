"""パス解決の共通化モジュール

jtr-generator/ ディレクトリとassets/配下のパスを一元管理します。
"""

from pathlib import Path


def get_skill_root() -> Path:
    """jtr-generator/ ディレクトリのルートパスを取得

    Returns:
        jtr-generator/ ディレクトリの絶対パス

    Note:
        このファイルは jtr-generator/scripts/jtr/helper/paths.py に配置されているため、
        parents[3] で jtr-generator/ ディレクトリを取得します：
        - parents[0]: jtr-generator/scripts/jtr/helper/
        - parents[1]: jtr-generator/scripts/jtr/
        - parents[2]: jtr-generator/scripts/
        - parents[3]: jtr-generator/
    """
    return Path(__file__).resolve().parents[3]


def get_assets_path(*parts: str) -> Path:
    """assets/配下のパスを取得

    Args:
        *parts: assets/ からの相対パス（複数指定可）

    Returns:
        jtr-generator/assets/ 配下の絶対パス

    Examples:
        >>> get_assets_path("config.yaml")
        PosixPath('/path/to/jtr-generator/assets/config.yaml')
        >>> get_assets_path("fonts", "BIZ_UDMincho", "BIZUDMincho-Regular.ttf")
        PosixPath('/path/to/jtr-generator/assets/fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf')
    """
    return get_skill_root() / "assets" / Path(*parts)


def get_schema_path(schema_name: str) -> Path:
    """スキーマファイルのパスを取得

    Args:
        schema_name: スキーマファイル名（例: "rirekisho_schema.json"）

    Returns:
        jtr-generator/assets/schemas/ 配下の絶対パス

    Examples:
        >>> get_schema_path("rirekisho_schema.json")
        PosixPath('/path/to/jtr-generator/assets/schemas/rirekisho_schema.json')
    """
    return get_assets_path("schemas", schema_name)


def get_layout_path(*parts: str) -> Path:
    """レイアウトデータのパスを取得

    Args:
        *parts: data/ からの相対パス（複数指定可）

    Returns:
        jtr-generator/assets/data/ 配下の絶対パス

    Examples:
        >>> get_layout_path("a4", "rirekisho_layout.json")
        PosixPath('/path/to/jtr-generator/assets/data/a4/rirekisho_layout.json')
    """
    return get_assets_path("data", *parts)
