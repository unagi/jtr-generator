# レイアウト座標の定義と再現手順

履歴書PDFの座標を「再現可能で説明可能な状態」に保つためのルールをまとめたものです。
座標の正当性は、罫線（セル境界）とフォントメトリクスに基づく計算で判断します。

## 対象ファイル
- `skill/data/a4/resume_layout.json`: 罫線・ラベル・データフィールドの絶対座標
- `skill/data/a4/rules/label_alignment.json`: ラベル配置のルール/手動ブロック
- `skill/data/a4/rules/field_alignment.json`: 入力データの配置ルール
- `skill/data/a4/definitions/manual_bounds.json`: 手動で測定した境界座標

## 用語と定義

### align（横方向）
- `left`: x を左端基準として描画
- `center`: x を中央基準として描画
- `right`: x を右端基準として描画

描画は ReportLab の `drawString` / `drawCentredString` / `drawRightString` に対応。

### valign（縦方向）
基準は **ベースライン**。フォントメトリクス（ascent / descent）で計算する。

- `baseline`: y をそのままベースラインとして使用
- `center`: セル中央に文字の見た目中心が来るようベースラインを計算
- `top`: セル上端から `ascent` と `margin_top` を引いた位置にベースライン
- `bottom`: セル下端から `descent` と `margin_bottom` を考慮した位置にベースライン

計算式（セルの上下は近傍の水平罫線から取得）:
```
center_baseline = cell_center - (ascent + descent) / 2
top_baseline    = cell_top - ascent - margin_top
bottom_baseline = cell_bottom - descent + margin_bottom
```

### margin
- `margin_left`: 左罫線からの x オフセット（align=leftで使用）
- `margin_top` / `margin_bottom`: valign=top/bottom の補正量

## 特殊ルール

### 電話ブロック（複数行）
`phone_block` / `contact_phone_block` は `phone` + `mobile` を結合し、1ブロックで描画する。

- `line_height`: 行間（ベースライン間隔）
- `max_lines`: 最大行数
- `margin_left` / `margin_top`: 上左余白

### 学歴・職歴の見出し行
`dynamic_rows` の `row_config.label` で、ラベル行のみセンタリングする。
通常行（年/月/本文）は `columns` の align に従う。

### 手動ブロック
写真欄の注記など、計算化できないブロックは `manual_blocks` で管理する。

## 再現手順

1. 罫線・ラベル・データフィールドの位置を `skill/data/a4/resume_layout.json` で調整
2. ラベルアンカーを再生成（`tests/fixtures/a4_text_anchors.json` に出力）
```
uv run python tools/layout/generate_text_anchors.py
```
3. ラベル/データの整合性をチェック
```
uv run python tools/layout/analyze_text_alignment.py
uv run python tools/layout/analyze_data_field_alignment.py
```
4. 許容誤差は `1.5pt`（それ以内は計算値を正として採用）

## 注意点
- フォントは `BIZ UDMincho` を前提とする（メトリクスが変わると計算値が変わる）。
- `valign=center` の結果はフォントサイズによって変わる。
- 目視調整は最終手段。計算値で合う場合は計算値を採用する。
