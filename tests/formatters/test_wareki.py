"""和暦変換機能のテスト"""

import pytest

from skill.scripts.jtr.generation_context import (
    GenerationContext,
    get_generation_context,
    init_generation_context,
    set_generation_context,
)
from skill.scripts.jtr.japanese_era import (
    JapaneseDateFormatter,
    convert_to_wareki,
    format_japanese_date,
    format_japanese_date_or_raw,
    format_seireki_japanese,
)


class TestConvertToWareki:
    """convert_to_wareki関数のテスト"""

    # 正常系: 令和（2019年5月1日〜）
    def test_reiwa_full_format_with_day(self) -> None:
        """令和の日付をfull形式（日付あり）に変換"""
        assert convert_to_wareki("2023-04-01", format="full") == "令和5年4月1日"
        assert convert_to_wareki("2024-12-15", format="full") == "令和6年12月15日"

    def test_reiwa_full_format_month_only(self) -> None:
        """令和の日付をfull形式（月のみ）に変換"""
        assert convert_to_wareki("2023-04", format="full") == "令和5年4月"
        assert convert_to_wareki("2024-12", format="full") == "令和6年12月"

    def test_reiwa_short_format_with_day(self) -> None:
        """令和の日付をshort形式（日付あり）に変換"""
        assert convert_to_wareki("2023-04-01", format="short") == "R5.4.1"
        assert convert_to_wareki("2024-12-15", format="short") == "R6.12.15"

    def test_reiwa_short_format_month_only(self) -> None:
        """令和の日付をshort形式（月のみ）に変換"""
        assert convert_to_wareki("2023-04", format="short") == "R5.4"
        assert convert_to_wareki("2024-12", format="short") == "R6.12"

    def test_reiwa_gannen(self) -> None:
        """令和元年（2019年5月1日）の変換"""
        assert convert_to_wareki("2019-05-01", format="full") == "令和元年5月1日"
        assert convert_to_wareki("2019-05", format="full") == "令和元年5月"
        assert convert_to_wareki("2019-05-01", format="short") == "R1.5.1"

    # 正常系: 平成（1989年1月8日〜2019年4月30日）
    def test_heisei_full_format_with_day(self) -> None:
        """平成の日付をfull形式（日付あり）に変換"""
        assert convert_to_wareki("2010-04-01", format="full") == "平成22年4月1日"
        assert convert_to_wareki("2019-04-30", format="full") == "平成31年4月30日"

    def test_heisei_full_format_month_only(self) -> None:
        """平成の日付をfull形式（月のみ）に変換"""
        assert convert_to_wareki("2010-04", format="full") == "平成22年4月"
        assert convert_to_wareki("2019-03", format="full") == "平成31年3月"

    def test_heisei_short_format_with_day(self) -> None:
        """平成の日付をshort形式（日付あり）に変換"""
        assert convert_to_wareki("2010-04-01", format="short") == "H22.4.1"
        assert convert_to_wareki("2019-04-30", format="short") == "H31.4.30"

    def test_heisei_gannen(self) -> None:
        """平成元年（1989年1月8日）の変換"""
        assert convert_to_wareki("1989-01-08", format="full") == "平成元年1月8日"
        # 注: 1989-01は月初日（1日）で判定するため昭和64年となる
        assert convert_to_wareki("1989-01", format="full") == "昭和64年1月"
        # 平成元年の月のみ表記は1989-02以降
        assert convert_to_wareki("1989-05", format="full") == "平成元年5月"

    # 正常系: 昭和（1926年12月25日〜1989年1月7日）
    def test_showa_full_format_with_day(self) -> None:
        """昭和の日付をfull形式（日付あり）に変換"""
        assert convert_to_wareki("1990-04-01", format="full") == "平成2年4月1日"
        assert convert_to_wareki("1989-01-07", format="full") == "昭和64年1月7日"
        assert convert_to_wareki("1980-06-15", format="full") == "昭和55年6月15日"

    def test_showa_full_format_month_only(self) -> None:
        """昭和の日付をfull形式（月のみ）に変換"""
        assert convert_to_wareki("1980-06", format="full") == "昭和55年6月"
        assert convert_to_wareki("1989-01", format="full") == "昭和64年1月"

    def test_showa_short_format_with_day(self) -> None:
        """昭和の日付をshort形式（日付あり）に変換"""
        assert convert_to_wareki("1980-06-15", format="short") == "S55.6.15"
        assert convert_to_wareki("1989-01-07", format="short") == "S64.1.7"

    def test_showa_gannen(self) -> None:
        """昭和元年（1926年12月25日）の変換"""
        assert convert_to_wareki("1926-12-25", format="full") == "昭和元年12月25日"
        # 注: 1926-12は月初日（1日）で判定するため範囲外となる
        # 昭和元年の月のみ表記は1927-01以降
        assert convert_to_wareki("1927-01", format="full") == "昭和2年1月"

    # デフォルトフォーマット
    def test_default_format_is_full(self) -> None:
        """formatパラメータ省略時はfull形式がデフォルト"""
        assert convert_to_wareki("2023-04-01") == "令和5年4月1日"

    # 異常系: 無効な日付形式
    def test_invalid_date_format_slash(self) -> None:
        """無効な日付形式（スラッシュ区切り）でValueErrorが発生"""
        with pytest.raises(ValueError) as exc_info:
            convert_to_wareki("2023/04/01")
        assert "invalid" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()

    def test_invalid_date_format_no_separator(self) -> None:
        """無効な日付形式（区切り文字なし）でValueErrorが発生"""
        with pytest.raises(ValueError):
            convert_to_wareki("20230401")

    def test_invalid_date_value(self) -> None:
        """無効な日付（存在しない日）でValueErrorが発生"""
        with pytest.raises(ValueError):
            convert_to_wareki("2023-13-01")  # 13月は存在しない

    def test_unsupported_era_before_showa(self) -> None:
        """対応外の年号（昭和より前）でValueErrorが発生"""
        with pytest.raises(ValueError) as exc_info:
            convert_to_wareki("1925-12-31")
        assert "unsupported" in str(exc_info.value).lower() or "era" in str(exc_info.value).lower()

    def test_invalid_format_parameter(self) -> None:
        """無効なformatパラメータでValueErrorが発生"""
        with pytest.raises(ValueError) as exc_info:
            convert_to_wareki("2023-04-01", format="invalid")  # type: ignore
        assert "format" in str(exc_info.value).lower()

    # エッジケース: 年号の境界
    def test_era_boundary_heisei_to_reiwa(self) -> None:
        """平成→令和の境界（2019年4月30日→5月1日）"""
        assert convert_to_wareki("2019-04-30", format="full") == "平成31年4月30日"
        assert convert_to_wareki("2019-05-01", format="full") == "令和元年5月1日"

    def test_era_boundary_showa_to_heisei(self) -> None:
        """昭和→平成の境界（1989年1月7日→8日）"""
        assert convert_to_wareki("1989-01-07", format="full") == "昭和64年1月7日"
        assert convert_to_wareki("1989-01-08", format="full") == "平成元年1月8日"


def test_format_seireki_japanese() -> None:
    assert format_seireki_japanese("1990-04-01", format_style="full") == "1990年4月1日"
    assert format_seireki_japanese("1990-04-01", format_style="short") == "1990.4.1"
    assert format_seireki_japanese("1990-04", format_style="full") == "1990年4月"
    assert format_seireki_japanese("1990-04", format_style="short") == "1990.4"


def test_format_japanese_date() -> None:
    assert format_japanese_date("2023-04-01", "seireki", format_style="full") == "2023年4月1日"
    assert format_japanese_date("2023-04-01", "seireki", format_style="short") == "2023.4.1"
    assert format_japanese_date("2023-04-01", "wareki", format_style="full") == "令和5年4月1日"
    assert format_japanese_date("2023-04-01", "wareki", format_style="short") == "R5.4.1"


def test_format_japanese_date_or_raw() -> None:
    assert format_japanese_date_or_raw("1990-04-01", "seireki", format_style="full") == (
        "1990年4月1日"
    )
    assert format_japanese_date_or_raw("1990/04/01", "seireki", format_style="full") == (
        "1990/04/01"
    )


def test_japanese_date_formatter() -> None:
    formatter = JapaneseDateFormatter("wareki", default_format_style="full")
    assert formatter.format("2023-04-01", format_style="short") == "R5.4.1"
    assert formatter.format_or_raw("2023-04", format_style="full") == "令和5年4月"
    assert formatter.format_or_raw("2023/04/01", format_style="full") == "2023/04/01"


def test_japanese_date_formatter_invalid_config() -> None:
    with pytest.raises(ValueError, match="date_format"):
        JapaneseDateFormatter("invalid")  # type: ignore
    with pytest.raises(ValueError, match="default_format_style"):
        JapaneseDateFormatter("seireki", default_format_style="inline")  # type: ignore


def test_format_japanese_date_invalid_format() -> None:
    with pytest.raises(ValueError, match="date_format"):
        format_japanese_date("2023-04-01", "invalid", format_style="full")  # type: ignore
    with pytest.raises(ValueError, match="format_style"):
        format_seireki_japanese("2023-04-01", format_style="inline")  # type: ignore


def test_generation_context_init_and_get() -> None:
    context = init_generation_context({"date_format": "wareki"})
    assert context.date_format == "wareki"
    assert context.date_formatter.format("2023-04-01") == "令和5年4月1日"
    assert get_generation_context().date_format == "wareki"


def test_generation_context_set_override() -> None:
    context = GenerationContext(
        date_format="seireki",
        date_formatter=JapaneseDateFormatter("seireki", default_format_style="full"),
    )
    set_generation_context(context)
    assert get_generation_context().date_format == "seireki"
