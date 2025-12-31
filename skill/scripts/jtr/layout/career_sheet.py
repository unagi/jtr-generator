"""職務経歴書のレイアウト定義読み込み。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..paths import get_assets_path

SpacingRules = tuple[dict[str, float], dict[str, float], dict[str, float]]


def load_career_sheet_spacing_rules() -> SpacingRules:
    rules_path = get_assets_path("data", "a4", "rules", "career_sheet_spacing.json")
    if not rules_path.exists():
        raise FileNotFoundError(f"余白ルールファイルが見つかりません: {rules_path}")

    try:
        with open(rules_path, encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"余白ルールファイルの読み込みに失敗しました: {rules_path}") from exc

    if not isinstance(loaded, dict):
        raise ValueError(f"余白ルールファイルの形式が不正です: {rules_path}")

    spacing_mm = _extract_numeric_map(loaded, "spacing_mm", rules_path)
    spacing_pt = _extract_numeric_map(loaded, "spacing_pt", rules_path)
    indent_mm = _extract_numeric_map(loaded, "indent_mm", rules_path)

    _ensure_required_keys(
        spacing_mm,
        {"xs", "sm", "md", "lg", "xl", "xxl", "xxxl"},
        "spacing_mm",
        rules_path,
    )
    _ensure_required_keys(
        spacing_pt,
        {
            "title_after",
            "h1_before",
            "h1_after",
            "h2_before",
            "h2_after",
            "h2_rule_before",
            "h2_rule_after",
            "h3_before",
            "h3_after",
            "h4_before",
            "h4_after",
            "h5_before",
            "h5_after",
            "h6_before",
            "h6_after",
            "h7_before",
            "h7_after",
            "body_after",
            "heading_bar_padding_x",
            "heading_bar_padding_y",
            "heading_bar_before",
            "heading_bar_after",
            "body_leading",
        },
        "spacing_pt",
        rules_path,
    )
    _ensure_required_keys(
        indent_mm,
        {"heading3", "heading4", "bullet_left", "bullet_hanging"},
        "indent_mm",
        rules_path,
    )

    return spacing_mm, spacing_pt, indent_mm


def _extract_numeric_map(loaded: dict[str, Any], key: str, rules_path: Path) -> dict[str, float]:
    raw = loaded.get(key)
    if not isinstance(raw, dict):
        raise ValueError(f"余白ルールの'{key}'が見つかりません: {rules_path}")
    result: dict[str, float] = {}
    for map_key, value in raw.items():
        if not isinstance(value, (int, float)):
            raise ValueError(f"余白ルールの'{key}.{map_key}'が数値ではありません: {rules_path}")
        result[map_key] = float(value)
    return result


def _ensure_required_keys(
    mapping: dict[str, float], required: set[str], name: str, rules_path: Path
) -> None:
    missing = required - mapping.keys()
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"余白ルールの'{name}'に必須キーが不足しています: {missing_list}")
