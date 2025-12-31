"""職務経歴書PDF生成のテスト"""

from pathlib import Path

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from skill.scripts.jtr.career_sheet_generator import generate_career_sheet_pdf


def test_generate_career_sheet_pdf_basic(tmp_path: Path) -> None:
    """基本的な職務経歴書PDF生成のテスト"""
    output_path = tmp_path / "test_career_sheet.pdf"

    # 最小限のデータ
    rirekisho_data = {
        "personal_info": {
            "name": "山田太郎",
            "birthdate": "1990-04-01",
            "phone": "090-1234-5678",
            "email": "yamada@example.com",
        }
    }

    markdown_content = """# 職務要約

データ分析領域で8年の経験。

## 職務経歴

### 株式会社○○（2020-04 〜 2023-03）

**カスタマーサクセス部門 マネージャー**
"""

    # フォント設定
    from skill.scripts.jtr.helper.fonts import find_default_font

    font_path = find_default_font()
    options = {"fonts": {"mincho": str(font_path)}}

    # PDF生成
    generate_career_sheet_pdf(rirekisho_data, markdown_content, options, output_path)

    # PDFファイルが生成されたことを確認
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_career_sheet_with_qualifications(tmp_path: Path) -> None:
    """免許・資格を含む職務経歴書のテスト"""
    output_path = tmp_path / "test_career_sheet_qualifications.pdf"

    rirekisho_data = {
        "personal_info": {
            "name": "山田太郎",
            "birthdate": "1990-04-01",
            "phone": "090-1234-5678",
            "email": "yamada@example.com",
        },
        "qualifications": [
            {"date": "2015-06", "name": "基本情報技術者試験 合格"},
            {"date": "2018-03", "name": "AWS Certified Solutions Architect - Associate"},
        ],
    }

    markdown_content = "# 職務要約\n\nテスト"

    from skill.scripts.jtr.helper.fonts import find_default_font

    font_path = find_default_font()
    options = {"fonts": {"mincho": str(font_path)}}

    generate_career_sheet_pdf(rirekisho_data, markdown_content, options, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_career_sheet_complex_markdown(tmp_path: Path) -> None:
    """複雑なMarkdownを含む職務経歴書のテスト"""
    output_path = tmp_path / "test_career_sheet_complex.pdf"

    rirekisho_data = {
        "personal_info": {
            "name": "山田太郎",
            "birthdate": "1990-04-01",
            "phone": "090-1234-5678",
            "email": "yamada@example.com",
        }
    }

    markdown_content = """# 職務要約

データ分析領域で**8年**の経験を持ちます。

## 職務経歴

### 株式会社○○（2020-04 〜 2023-03）

#### 担当業務と実績

- 顧客インタビュー20社実施
- オンボーディングプログラム再設計
- チャーンリスク予測モデル構築

### 株式会社△△（2015-04 〜 2020-03）

#### 主な業務

売上予測モデルの構築により**予測精度40%向上**を達成しました。

## 活かせるスキル

- Python（5年）
- AWS（3年）
- SQL（7年）
"""

    from skill.scripts.jtr.helper.fonts import find_default_font

    font_path = find_default_font()
    options = {"fonts": {"mincho": str(font_path)}}

    generate_career_sheet_pdf(rirekisho_data, markdown_content, options, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_font_not_found_error(tmp_path: Path) -> None:
    """存在しないフォントパス指定時のエラー"""
    output_path = tmp_path / "test_error.pdf"

    rirekisho_data = {"personal_info": {"name": "Test", "email": "test@example.com"}}
    markdown_content = "# Test"
    options = {"fonts": {"mincho": "/nonexistent/font.ttf"}}

    with pytest.raises(FileNotFoundError):
        generate_career_sheet_pdf(rirekisho_data, markdown_content, options, output_path)
