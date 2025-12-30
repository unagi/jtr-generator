"""
PDF生成テスト（データフィールド付き）

Phase 1: 個人情報フィールドの生成テスト
"""

from datetime import date

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from skill.jtr.pdf_generator import (
    _calculate_age,
    _format_date,
    _get_field_value,
    generate_resume_pdf,
)


@pytest.fixture
def sample_data():
    """テスト用のサンプルデータ"""
    return {
        "personal_info": {
            "name": "山田太郎",
            "name_kana": "やまだたろう",
            "birthdate": "1990-04-01",
            "gender": "男性",
            "postal_code": "150-0041",
            "address": "東京都渋谷区神南1-1-1",
            "phone": "03-1234-5678",
            "mobile": "090-1234-5678",
        },
        "education": [],
        "work_history": [],
        "qualifications": [],
    }


def test_generate_resume_with_personal_info(sample_data, tmp_path):
    """個人情報フィールド付き履歴書の生成"""
    output_path = tmp_path / "resume_with_data.pdf"
    generate_resume_pdf(sample_data, {"paper_size": "A4", "date_format": "seireki"}, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_resume_with_wareki_format(sample_data, tmp_path):
    """和暦フォーマットでの履歴書生成"""
    output_path = tmp_path / "resume_wareki.pdf"
    generate_resume_pdf(sample_data, {"paper_size": "A4", "date_format": "wareki"}, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_calculate_age():
    """年齢計算のユニットテスト"""
    # 基本的な年齢計算
    age = _calculate_age("1990-04-01", date(2023, 12, 29))
    assert age == 33

    # 誕生日前（年齢は増えない）
    age = _calculate_age("1990-04-01", date(2024, 3, 31))
    assert age == 33

    # 誕生日当日（年齢が増える）
    age = _calculate_age("1990-04-01", date(2024, 4, 1))
    assert age == 34

    # 誕生日後
    age = _calculate_age("1990-04-01", date(2024, 4, 2))
    assert age == 34


def test_calculate_age_invalid_format():
    """無効な日付形式でValueErrorが発生すること"""
    with pytest.raises(ValueError, match="Invalid birthdate format"):
        _calculate_age("1990/04/01")


def test_format_date_seireki():
    """西暦フォーマットのテスト"""
    # full形式
    result = _format_date("1990-04-01", "seireki", "full")
    assert result == "1990年4月1日"

    # inline形式
    result = _format_date("1990-04-01", "seireki", "inline")
    assert result == "1990 年 4 月 1 日"

    # short形式
    result = _format_date("1990-04-01", "seireki", "short")
    assert result == "1990.4.1"


def test_format_date_wareki():
    """和暦フォーマットのテスト"""
    # full形式
    result = _format_date("2023-04-01", "wareki", "full")
    assert result == "令和5年4月1日"

    # inline形式（スペース区切り）
    result = _format_date("2023-04-01", "wareki", "inline")
    assert "令和" in result and "5" in result and "4" in result and "1" in result

    # short形式
    result = _format_date("2023-04-01", "wareki", "short")
    assert result == "R5.4.1"


def test_format_date_wareki_gannen():
    """和暦元年のテスト"""
    result = _format_date("2019-05-01", "wareki", "full")
    assert result == "令和元年5月1日"


def test_format_date_invalid_format():
    """無効な日付フォーマットでValueErrorが発生すること"""
    with pytest.raises(ValueError, match="Invalid date format"):
        _format_date("2023/04/01", "seireki", "full")


def test_get_field_value():
    """フィールド値取得のテスト"""
    data = {
        "personal_info": {
            "name": "山田太郎",
            "birthdate": "1990-04-01",
        }
    }

    # 通常の値取得
    assert _get_field_value(data, "personal_info.name") == "山田太郎"
    assert _get_field_value(data, "personal_info.birthdate") == "1990-04-01"

    # 年齢計算（transformあり）
    age_str = _get_field_value(data, "personal_info.birthdate", transform="calculate_age")
    assert age_str.isdigit()  # 数値文字列であることを確認


def test_get_field_value_missing_field():
    """存在しないフィールドでKeyErrorが発生すること"""
    data = {"personal_info": {"name": "山田太郎"}}

    with pytest.raises(KeyError):
        _get_field_value(data, "personal_info.missing_field")


def test_backward_compatibility_blank_resume(tmp_path):
    """後方互換性: 空のdataでブランク履歴書が生成される"""
    output_path = tmp_path / "blank_resume.pdf"

    # 空のdataで生成
    generate_resume_pdf({}, {"paper_size": "A4"}, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_backward_compatibility_empty_sections(tmp_path):
    """後方互換性: 空のセクションでブランク履歴書が生成される"""
    output_path = tmp_path / "blank_resume2.pdf"

    # すべてのセクションが空
    data = {
        "personal_info": {},
        "education": [],
        "work_history": [],
        "qualifications": [],
    }

    generate_resume_pdf(data, {"paper_size": "A4"}, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_resume_with_education_and_work_history(tmp_path):
    """学歴・職歴フィールド付き履歴書の生成"""
    data = {
        "personal_info": {
            "name": "山田太郎",
            "name_kana": "やまだたろう",
            "birthdate": "1990-04-01",
            "gender": "男性",
            "postal_code": "150-0041",
            "address": "東京都渋谷区神南1-1-1",
            "address_kana": "とうきょうとしぶやくじんなん",
            "phone": "03-1234-5678",
            "mobile": "090-1234-5678",
        },
        "education": [
            {"date": "2006-03", "type": "卒業", "school": "東京都立〇〇高等学校"},
            {
                "date": "2010-03",
                "type": "卒業",
                "school": "〇〇大学",
                "department": "工学部 情報工学科",
            },
        ],
        "work_history": [
            {"date": "2010-04", "type": "入社", "company": "株式会社〇〇"},
            {
                "date": "2015-03",
                "type": "退職",
                "company": "株式会社〇〇",
                "note": "一身上の都合により",
            },
            {"date": "2015-04", "type": "入社", "company": "株式会社△△"},
        ],
        "qualifications": [],
    }

    output_path = tmp_path / "resume_with_education_work_history.pdf"
    generate_resume_pdf(data, {"paper_size": "A4", "date_format": "seireki"}, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_resume_with_education_wareki_format(tmp_path):
    """学歴・職歴を和暦フォーマットで生成"""
    data = {
        "personal_info": {
            "name": "山田太郎",
            "name_kana": "やまだたろう",
            "birthdate": "1990-04-01",
            "gender": "男性",
            "postal_code": "150-0041",
            "address": "東京都渋谷区神南1-1-1",
            "address_kana": "とうきょうとしぶやくじんなん",
            "phone": "03-1234-5678",
            "mobile": "090-1234-5678",
        },
        "education": [
            {"date": "2006-03", "type": "卒業", "school": "東京都立〇〇高等学校"},
        ],
        "work_history": [
            {"date": "2010-04", "type": "入社", "company": "株式会社〇〇"},
        ],
        "qualifications": [],
    }

    output_path = tmp_path / "resume_education_wareki.pdf"
    generate_resume_pdf(data, {"paper_size": "A4", "date_format": "wareki"}, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_format_content():
    """_format_content関数のテスト"""
    from skill.jtr.pdf_generator import _format_content

    # 学歴（department付き）
    item = {"school": "〇〇大学", "department": "工学部"}
    result = _format_content(item, "{school}{department}")
    assert result == "〇〇大学 工学部"

    # 学歴（departmentなし）
    item = {"school": "東京都立〇〇高等学校"}
    result = _format_content(item, "{school}{department}")
    assert result == "東京都立〇〇高等学校"

    # 職歴（note付き）
    item = {"company": "株式会社〇〇", "type": "退職", "note": "一身上の都合により"}
    result = _format_content(item, "{company} {type}{note}")
    assert result == "株式会社〇〇 退職 一身上の都合により"

    # 職歴（noteなし）
    item = {"company": "株式会社△△", "type": "入社"}
    result = _format_content(item, "{company} {type}{note}")
    assert result == "株式会社△△ 入社"
