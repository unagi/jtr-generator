"""
履歴書PDF生成モジュール

このモジュールは、事前に抽出された罫線データ（JSON）を使用して
JIS規格準拠の履歴書PDFを生成します。
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from src.formatters.wareki import convert_to_wareki


def _find_default_font() -> Path:
    """
    デフォルトフォント（BIZ UDMincho）のパスを取得

    Returns:
        デフォルトフォントの絶対パス

    Raises:
        FileNotFoundError: フォントファイルが存在しない場合
    """
    base_dir = Path(__file__).parent.parent.parent
    font_dir = base_dir / "fonts/BIZ_UDMincho"

    # Phase 1の選定結果に基づき、.ttfファイルを検索
    # Regular/Boldどちらかが残っている前提
    candidates = list(font_dir.glob("*.ttf"))

    if not candidates:
        raise FileNotFoundError(
            f"Default font not found in {font_dir}\n"
            "Please ensure BIZ UDMincho font is installed or configure custom font in options['fonts']."
        )

    # 最初に見つかったフォントを使用
    return candidates[0]


def _register_font(font_path: Path | None = None) -> str:
    """
    TrueTypeフォントをReportLabに登録

    Args:
        font_path: フォントファイルのパス（Noneの場合はデフォルト使用）

    Returns:
        登録されたフォント名

    Raises:
        FileNotFoundError: フォントファイルが存在しない場合
    """
    if font_path is None:
        font_path = _find_default_font()

    if not font_path.exists():
        raise FileNotFoundError(
            f"Font file not found: {font_path}\n"
            "Please ensure the font file exists or configure custom font in options['fonts']."
        )

    # フォント名はファイル名から生成（拡張子除く）
    font_name = font_path.stem
    pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    return font_name


def generate_resume_pdf(
    data: dict[str, Any],
    options: dict[str, Any],
    output_path: Path,
) -> None:
    """
    履歴書PDFを生成する（v4: 罫線+固定ラベル+データフィールド）

    Args:
        data: 履歴書データ（personal_info, education, work_history等）
        options: 生成オプション（paper_size, date_format, fonts等）
        output_path: 出力先PDFファイルパス
    """
    # レイアウトデータのJSONファイルパス（v4フォーマット）
    # TODO: options経由で指定できるようにする（A4/B5切り替え対応）
    layout_json_path = Path(__file__).parent.parent.parent / "data/layouts/resume_layout_a4_v2.json"

    with open(layout_json_path, encoding="utf-8") as f:
        layout_data = json.load(f)

    # A4サイズのCanvasを作成
    c = canvas.Canvas(str(output_path), pagesize=A4)

    # フォント登録（options['fonts']['main']を優先、未指定時はデフォルト）
    custom_font_path = None
    if "fonts" in options and "main" in options["fonts"]:
        custom_font_path = Path(options["fonts"]["main"])

    font_name = _register_font(custom_font_path)

    # 後方互換性: dataが空ならブランク履歴書
    is_blank = not data or all(not v for v in data.values())

    # 日付フォーマット取得
    date_format = options.get("date_format", "seireki")

    # Page 1: 罫線 + 固定ラベル + データフィールド
    _draw_lines(c, layout_data["page1_lines"])
    if "page1_texts" in layout_data:  # v3フォーマット対応（後方互換性）
        _draw_texts(c, layout_data["page1_texts"], font_name)

    # v4フォーマット: データフィールド描画
    remaining_rows = None
    if not is_blank and "page1_data_fields" in layout_data:
        _draw_data_fields(c, data, layout_data["page1_data_fields"], font_name, date_format)

        # 学歴・職歴（page1部分）の描画と、page2への継続を管理
        if "education_work_history_p1" in layout_data["page1_data_fields"]:
            remaining_rows = _draw_education_work_history(
                c, data, layout_data["page1_data_fields"]["education_work_history_p1"],
                font_name, date_format, None
            )

    c.showPage()

    # Page 2: 罫線 + 固定ラベル + データフィールド
    _draw_lines(c, layout_data["page2_lines"])
    if "page2_texts" in layout_data:
        _draw_texts(c, layout_data["page2_texts"], font_name)

    # v4フォーマット: page2データフィールド描画（学歴・職歴の続き + 資格 + 志望動機等）
    if not is_blank and "page2_data_fields" in layout_data:
        # 学歴・職歴の続き（remaining_rowsがある場合のみ）
        if remaining_rows and "education_work_history_p2" in layout_data["page2_data_fields"]:
            _draw_education_work_history(
                c, data, layout_data["page2_data_fields"]["education_work_history_p2"],
                font_name, date_format, remaining_rows
            )

        # 資格・免許
        if "qualifications" in layout_data["page2_data_fields"]:
            _draw_education_work_history(
                c, data, layout_data["page2_data_fields"]["qualifications"],
                font_name, date_format, None
            )

        # 志望動機・自己PR・本人希望（複数行テキスト）
        for field_key in ["motivation_self_pr", "hope"]:
            if field_key in layout_data["page2_data_fields"]:
                _draw_multiline_text(
                    c, data, layout_data["page2_data_fields"][field_key], font_name
                )

    c.showPage()

    c.save()


def _calculate_age(birthdate_str: str, reference_date: date | None = None) -> int:
    """
    生年月日から年齢を計算

    Args:
        birthdate_str: ISO 8601形式の生年月日（YYYY-MM-DD）
        reference_date: 基準日（Noneの場合は今日の日付）

    Returns:
        年齢

    Raises:
        ValueError: 無効な日付形式
    """
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid birthdate format: {birthdate_str}. Expected YYYY-MM-DD") from e

    if reference_date is None:
        reference_date = date.today()

    # 年齢計算（誕生日前後で判定）
    age = reference_date.year - birthdate.year
    if (reference_date.month, reference_date.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


def _format_date(
    date_str: str,
    date_format: Literal["seireki", "wareki"],
    format_style: Literal[
        "full", "short", "inline", "inline_spaced", "wareki_year_only", "month_only", "day_only"
    ] = "full",
) -> str:
    """
    日付を指定フォーマットで整形

    Args:
        date_str: ISO 8601形式の日付（YYYY-MM-DD）
        date_format: "seireki"（西暦）または "wareki"（和暦）
        format_style: "full"（令和5年4月1日）、"short"（R5.4.1）、"inline"（スペース区切り）、
                     "inline_spaced"（数字もスペース区切り）、"wareki_year_only"（平成 2）、
                     "month_only"（4）、"day_only"（1）

    Returns:
        整形された日付文字列

    Raises:
        ValueError: 無効な日付形式またはフォーマット指定
    """
    # 日付をパース
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD") from e

    # 部分抽出フォーマット
    if format_style == "wareki_year_only":
        # 年部分のみ（和暦 or 西暦）
        if date_format == "wareki":
            # 和暦の年部分のみ（例: "平成 2"）
            full_str = convert_to_wareki(date_str, format="full")
            # "令和5年4月1日" → "令和 5"
            year_part = full_str.split("年")[0]
            import re

            result = re.sub(r"(\D)(\d)", r"\1 \2", year_part)
            return result
        else:  # seireki
            # 西暦の年のみ（例: "1990"）
            return str(parsed_date.year)
    elif format_style == "month_only":
        return str(parsed_date.month)
    elif format_style == "day_only":
        return str(parsed_date.day)

    # 通常のフォーマット
    if date_format == "wareki":
        if format_style == "inline":
            # 和暦でスペース区切り形式（例: "令和 5 年 4 月 1 日"）
            full_str = convert_to_wareki(date_str, format="full")
            # "令和5年4月1日" → "令和 5 年 4 月 1 日"
            return full_str.replace("年", " 年 ").replace("月", " 月 ").replace("日", " 日")
        elif format_style == "inline_spaced":
            # 和暦で完全スペース区切り（例: "令和 5 年 4 月 1 日生"）
            full_str = convert_to_wareki(date_str, format="full")
            # "令和5年4月1日" → "令和 5 年 4 月 1 日"（各要素間にスペース）
            import re

            result = re.sub(r"(\D)(\d)", r"\1 \2", full_str)  # 文字と数字の間
            result = re.sub(r"(\d)(\D)", r"\1 \2", result)  # 数字と文字の間
            return result
        else:
            return convert_to_wareki(date_str, format=format_style)
    elif date_format == "seireki":
        # 西暦形式
        if format_style == "full":
            return f"{parsed_date.year}年{parsed_date.month}月{parsed_date.day}日"
        elif format_style == "inline":
            return f"{parsed_date.year} 年 {parsed_date.month} 月 {parsed_date.day} 日"
        elif format_style == "inline_spaced":
            return f"{parsed_date.year} 年 {parsed_date.month} 月 {parsed_date.day} 日"
        elif format_style == "short":
            return f"{parsed_date.year}.{parsed_date.month}.{parsed_date.day}"
        else:
            raise ValueError(f"Invalid format_style: {format_style}")
    else:
        raise ValueError(f"Invalid date_format: {date_format}. Expected 'seireki' or 'wareki'")


def _get_field_value(
    data: dict[str, Any], field_path: str, transform: str | None = None
) -> str:
    """
    データからフィールド値を取得し、必要に応じて変換

    Args:
        data: 履歴書データ
        field_path: "personal_info.name"のようなドット区切りパス
        transform: "calculate_age"等の変換指示

    Returns:
        表示用の文字列

    Raises:
        KeyError: フィールドが存在しない場合
    """
    # ドット区切りパスからネストした値を取得
    keys = field_path.split(".")
    value: Any = data
    for key in keys:
        value = value[key]

    # 変換処理
    if transform == "calculate_age":
        return str(_calculate_age(str(value)))
    else:
        return str(value)


def _draw_data_fields(
    c: canvas.Canvas,
    data: dict[str, Any],
    field_defs: dict[str, Any],
    font_name: str,
    date_format: Literal["seireki", "wareki"] = "seireki",
) -> None:
    """
    個人情報フィールドを描画（v4フォーマット対応）

    Args:
        c: ReportLabのCanvasオブジェクト
        data: 履歴書データ（personal_infoセクション含む）
        field_defs: レイアウトJSONのpage1_data_fields
        font_name: 登録済みフォント名
        date_format: 日付フォーマット（"seireki" or "wareki"）
    """
    for _field_key, field_def in field_defs.items():
        # 動的行フィールド（学歴・職歴）はスキップ（別途処理）
        if field_def.get("type") == "dynamic_rows":
            continue

        # フィールド値を取得
        try:
            field_path = field_def["field_path"]
            transform = field_def.get("transform")
            value = _get_field_value(data, field_path, transform)

            # 日付フィールドの特別処理
            if "format" in field_def:
                format_map: dict[str, Literal["full", "short", "inline", "inline_spaced", "wareki_year_only", "month_only", "day_only"]] = {
                    "wareki_inline": "inline",
                    "wareki_inline_spaced": "inline_spaced",
                    "wareki_year_only": "wareki_year_only",
                    "month_only": "month_only",
                    "day_only": "day_only",
                }
                format_style: Literal["full", "short", "inline", "inline_spaced", "wareki_year_only", "month_only", "day_only"] = format_map.get(field_def["format"], "full")
                value = _format_date(value, date_format, format_style)

            # フォント設定
            c.setFont(font_name, field_def["font_size"])
            c.setFillColorRGB(0, 0, 0)

            # 配置方向に応じた描画
            align = field_def.get("align", "left")
            if align == "left":
                c.drawString(field_def["x"], field_def["y"], value)
            elif align == "center":
                c.drawCentredString(field_def["x"], field_def["y"], value)
            elif align == "right":
                c.drawRightString(field_def["x"], field_def["y"], value)

        except KeyError:
            # フィールドが存在しない場合はスキップ（オプショナルフィールド対応）
            continue


def _draw_texts(
    c: canvas.Canvas,
    texts: list[dict[str, Any]],
    font_name: str,
) -> None:
    """
    固定テキストラベルを描画する（v3フォーマット対応）

    Args:
        c: ReportLabのCanvasオブジェクト
        texts: テキストデータのリスト（dict形式、v3フォーマット）
        font_name: 登録済みのフォント名
    """
    for text in texts:
        # フォント設定
        c.setFont(font_name, text["font_size"])

        # 色設定（黒固定）
        c.setFillColorRGB(0, 0, 0)

        # 配置方向に応じた描画
        align = text.get("align", "left")
        if align == "left":
            c.drawString(text["x"], text["y"], text["text"])
        elif align == "center":
            c.drawCentredString(text["x"], text["y"], text["text"])
        elif align == "right":
            c.drawRightString(text["x"], text["y"], text["text"])


def _draw_lines(c: canvas.Canvas, lines: list[dict[str, Any]]) -> None:
    """
    罫線を完全な描画設定で描画する（v2フォーマット対応）

    Args:
        c: ReportLabのCanvasオブジェクト
        lines: 線分データのリスト（dict形式、v2フォーマット）
    """
    for line in lines:
        # 線幅設定
        c.setLineWidth(line["width"])

        # 線種設定（破線パターン）
        dash_pattern = line.get("dash_pattern", [])
        dash_phase = line.get("dash_phase", 0)
        if dash_pattern and len(dash_pattern) > 0:
            # ReportLabは偶数要素を期待（奇数の場合は2回繰り返して周期維持）
            if len(dash_pattern) % 2 != 0:
                dash_pattern = dash_pattern * 2
            c.setDash(dash_pattern, dash_phase)
        else:
            c.setDash()  # 実線にリセット

        # 端部形状設定（0=butt, 1=round, 2=square）
        cap = line.get("cap", 2)
        c.setLineCap(cap)

        # 接合形状設定（0=mitre, 1=round, 2=bevel）
        join = line.get("join", 1)
        c.setLineJoin(join)

        # 色設定（RGB: 0.0-1.0）
        color = line.get("color", [0.0, 0.0, 0.0])
        c.setStrokeColorRGB(*color)

        # 線を描画
        c.line(line["x0"], line["y0"], line["x1"], line["y1"])


def _draw_education_work_history(
    c: canvas.Canvas,
    data: dict[str, Any],
    field_def: dict[str, Any],
    font_name: str,
    date_format: Literal["seireki", "wareki"],
    pending_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]] | None:
    """
    学歴・職歴フィールドを描画（page1またはpage2）

    Args:
        c: ReportLabのCanvasオブジェクト
        data: 履歴書データ（education, work_historyセクション含む）
        field_def: レイアウトJSONのeducation_work_historyフィールド定義
        font_name: 登録済みフォント名
        date_format: 日付フォーマット（\"seireki\" or \"wareki\"）
        pending_rows: page1から継続する未描画行（page2の場合のみ）

    Returns:
        次ページに継続する未描画行（あれば）
    """
    if field_def.get("type") != "dynamic_rows":
        return None

    row_config = field_def["row_config"]
    data_sources = field_def["data_sources"]
    max_rows = field_def.get("max_rows", 100)  # デフォルト100行

    # フォント設定
    font_size = row_config["font_size"]
    c.setFont(font_name, font_size)
    c.setFillColorRGB(0, 0, 0)

    # 行のbaseline計算
    first_baseline = row_config["first_row_baseline"]
    row_height = row_config["row_height"]

    current_row = 0
    all_rows = []

    # pending_rowsがある場合（page2での継続）
    if pending_rows:
        all_rows = pending_rows
    else:
        # 全行を生成（page1の場合）
        for source in data_sources:
            label = source["label"]
            field_path = source["field_path"]
            content_format = source["content_format"]

            # データ取得
            try:
                items = data[field_path]
            except KeyError:
                continue

            # ラベル行（空文字列の場合はスキップ）
            if label:
                all_rows.append({"content": label, "is_label": True})

            # データ行
            for item in items:
                date_str = item["date"]  # YYYY-MM形式
                year_str = _format_date(date_str + "-01", date_format, "wareki_year_only")
                month_str = _format_date(date_str + "-01", date_format, "month_only")
                content = _format_content(item, content_format)

                all_rows.append({
                    "year": year_str,
                    "month": month_str,
                    "content": content,
                    "is_label": False,
                })

    # このページで描画できる行数まで描画
    rows_to_draw = all_rows[:max_rows]
    remaining_rows = all_rows[max_rows:] if len(all_rows) > max_rows else None

    for row_data in rows_to_draw:
        current_baseline = first_baseline - (current_row * row_height)
        _draw_row(
            c,
            row_data,
            current_baseline,
            row_config["columns"],
            font_name,
            font_size,
            date_format,
        )
        current_row += 1

    return remaining_rows


def _format_content(item: dict[str, Any], format_template: str) -> str:
    """
    データ項目から内容文字列を整形

    Args:
        item: データ項目（education or work_history）
        format_template: フォーマットテンプレート（例: \"{school}{department}\"）

    Returns:
        整形された文字列
    """
    # テンプレート内のプレースホルダーを置換
    result = format_template

    # 各フィールドを取得して置換
    for key in ["school", "department", "company", "type", "note", "name"]:
        placeholder = "{" + key + "}"
        if placeholder in result:
            value = item.get(key, "")
            # 後続フィールド（department, type, note）は、プレースホルダーの直前にスペースがない場合のみ
            # 自動でスペースを追加（存在する場合）
            # nameフィールドは資格名なのでスペース追加不要
            if key in ["department", "type", "note"] and value:
                idx = result.find(placeholder)
                if idx > 0 and result[idx - 1] != " ":
                    value = " " + value
            result = result.replace(placeholder, value)

    return result


def _draw_row(
    c: canvas.Canvas,
    row_data: dict[str, str],
    baseline_y: float,
    columns: dict[str, Any],
    font_name: str,
    font_size: float,
    date_format: Literal["seireki", "wareki"],
) -> None:
    """
    1行分のデータを描画

    Args:
        c: ReportLabのCanvasオブジェクト
        row_data: 行データ（year, month, content等）
        baseline_y: 行のbaseline Y座標
        columns: 列定義（レイアウトJSONのcolumns）
        font_name: 登録済みフォント名
        font_size: フォントサイズ
        date_format: 日付フォーマット
    """
    c.setFont(font_name, font_size)
    c.setFillColorRGB(0, 0, 0)

    for _col_name, col_config in columns.items():
        field_key = col_config["field_key"]
        value = row_data.get(field_key, "")

        if not value:
            continue

        x = col_config["x"]
        align = col_config["align"]

        if align == "left":
            c.drawString(x, baseline_y, value)
        elif align == "center":
            c.drawCentredString(x, baseline_y, value)
        elif align == "right":
            c.drawRightString(x, baseline_y, value)


def _draw_multiline_text(
    c: canvas.Canvas,
    data: dict[str, Any],
    field_def: dict[str, Any],
    font_name: str,
) -> None:
    """
    複数行テキストフィールドを描画（志望動機、自己PR、本人希望）

    Args:
        c: ReportLabのCanvasオブジェクト
        data: 履歴書データ
        field_def: レイアウトJSONのフィールド定義
        font_name: 登録済みフォント名
    """
    if field_def.get("type") != "multiline_text":
        return

    # フィールド値を取得（複数フィールドの統合をサポート）
    text_parts = []

    if "field_paths" in field_def:
        # 複数フィールドを統合
        separator = field_def.get("separator", "\n\n")
        for field_path in field_def["field_paths"]:
            try:
                value = _get_field_value(data, field_path)
                if value:
                    text_parts.append(value)
            except KeyError:
                continue
        text = separator.join(text_parts) if text_parts else None
    elif "field_path" in field_def:
        # 単一フィールド
        try:
            text = _get_field_value(data, field_def["field_path"])
        except KeyError:
            return
    else:
        return

    if not text:
        return

    # 設定取得
    x = field_def["x"]
    y_top = field_def["y_top"]
    y_bottom = field_def["y_bottom"]
    width = field_def["width"]
    font_size = field_def["font_size"]
    line_height = field_def["line_height"]

    # フォント設定
    c.setFont(font_name, font_size)
    c.setFillColorRGB(0, 0, 0)

    # テキストを行に分割（改行コードで分割）
    lines = text.split("\n")

    # 各行を描画
    current_y = y_top
    for line in lines:
        if current_y < y_bottom:
            break  # 領域を超えたら終了

        # 行が長すぎる場合は折り返し
        wrapped_lines = _wrap_text(c, line, width, font_name, font_size)

        for wrapped_line in wrapped_lines:
            if current_y < y_bottom:
                break

            c.drawString(x, current_y, wrapped_line)
            current_y -= line_height


def _wrap_text(
    c: canvas.Canvas, text: str, max_width: float, font_name: str, font_size: float
) -> list[str]:
    """
    テキストを指定幅で折り返し

    Args:
        c: ReportLabのCanvasオブジェクト
        text: 折り返すテキスト
        max_width: 最大幅（pt）
        font_name: フォント名
        font_size: フォントサイズ

    Returns:
        折り返された行のリスト
    """
    if not text:
        return [""]

    # 文字列の幅を測定
    c.setFont(font_name, font_size)
    text_width = c.stringWidth(text, font_name, font_size)

    if text_width <= max_width:
        return [text]

    # 折り返しが必要な場合
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        test_width = c.stringWidth(test_line, font_name, font_size)

        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines
