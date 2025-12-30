"""和暦変換ユーティリティ"""

from datetime import date, datetime
from typing import Literal

# 年号の定義（開始日、年号名、略称）
_ERA_DEFINITIONS = [
    (date(2019, 5, 1), "令和", "R"),
    (date(1989, 1, 8), "平成", "H"),
    (date(1926, 12, 25), "昭和", "S"),
]


def _parse_date_string(date_str: str) -> tuple[date, bool]:
    """
    日付文字列をパースしてdateオブジェクトと月のみフラグを返す

    Args:
        date_str: YYYY-MM-DD または YYYY-MM 形式の日付文字列

    Returns:
        (dateオブジェクト, 月のみフラグ)

    Raises:
        ValueError: 無効な日付形式
    """
    # YYYY-MM-DD形式
    if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return (parsed_date, False)
        except ValueError as e:
            raise ValueError(f"Invalid date value: {date_str}") from e

    # YYYY-MM形式
    if len(date_str) == 7 and date_str[4] == "-":
        try:
            parsed_date = datetime.strptime(date_str + "-01", "%Y-%m-%d").date()
            return (parsed_date, True)
        except ValueError as e:
            raise ValueError(f"Invalid date value: {date_str}") from e

    raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD or YYYY-MM format.")


def _get_era_info(target_date: date) -> tuple[str, str, int]:
    """
    指定日付の年号情報を取得

    Args:
        target_date: 対象日付

    Returns:
        (年号名, 略称, 和暦年)

    Raises:
        ValueError: 対応していない年号範囲
    """
    for era_start, era_name, era_abbrev in _ERA_DEFINITIONS:
        if target_date >= era_start:
            # 和暦年を計算
            wareki_year = target_date.year - era_start.year + 1
            return (era_name, era_abbrev, wareki_year)

    raise ValueError(
        f"Unsupported era: {target_date}. Only dates from Showa (1926-12-25) onwards are supported."
    )


def convert_to_wareki(date_str: str, format: Literal["full", "short"] = "full") -> str:
    """
    西暦日付を和暦に変換

    Args:
        date_str: YYYY-MM-DD または YYYY-MM 形式の日付文字列
        format: 'full' または 'short'
            - 'full': "令和5年4月1日" または "令和5年4月"
            - 'short': "R5.4.1" または "R5.4"

    Returns:
        和暦形式の日付文字列

    Raises:
        ValueError: 無効な日付形式、対応していない年号範囲、または無効なformatパラメータ

    Examples:
        >>> convert_to_wareki("2023-04-01", format="full")
        '令和5年4月1日'
        >>> convert_to_wareki("2023-04", format="full")
        '令和5年4月'
        >>> convert_to_wareki("2023-04-01", format="short")
        'R5.4.1'
        >>> convert_to_wareki("2019-05-01", format="full")
        '令和元年5月1日'
    """
    # formatパラメータの検証
    if format not in {"full", "short"}:
        raise ValueError(f"Invalid format parameter: {format}. Expected 'full' or 'short'.")

    # 日付文字列をパース
    parsed_date, month_only = _parse_date_string(date_str)

    # 年号情報を取得
    era_name, era_abbrev, wareki_year = _get_era_info(parsed_date)

    # 元年表記
    year_display = "元" if wareki_year == 1 else str(wareki_year)

    # フォーマットに応じて出力
    if format == "full":
        if month_only:
            return f"{era_name}{year_display}年{parsed_date.month}月"
        else:
            return f"{era_name}{year_display}年{parsed_date.month}月{parsed_date.day}日"
    else:  # short
        year_display_short = "1" if wareki_year == 1 else str(wareki_year)
        if month_only:
            return f"{era_abbrev}{year_display_short}.{parsed_date.month}"
        else:
            return f"{era_abbrev}{year_display_short}.{parsed_date.month}.{parsed_date.day}"
