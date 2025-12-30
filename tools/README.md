# tools

`tests/fixtures/R3_pdf_rirekisyo.pdf` を解析し、コード側のレイアウト・フォント調整に
反映するためのワークスペースです。生成系のコードとは分離し、PDFの罫線やテキスト配置
を検証するツールだけを配置しています。

## 主要スクリプト

- `extract_lines.py`: 参照PDFから罫線を抽出し、`data/layouts/resume_layout_a4_v2.json` を更新します。
- `font_metrics_report.py`: フォントメトリクスに基づき、氏名欄・学歴/職歴行・ふりがな欄のベースラインを一括で確認するJSONレポートを生成します。
- `generate_blank_resume.py`: 現在のレイアウトで罫線のみのPDFを生成します。
- `verify_pdf.py`: 生成したPDFのページサイズなどの基本情報を表示します。

### layout サブディレクトリ

`tools/layout/` はテキスト位置やデータフィールドの整合性を解析するスクリプトをまとめています。

- `analyze_data_field_alignment.py`: データフィールドと罫線の整合性を検証するレポートを生成。
- `analyze_text_alignment.py`: テキストラベルの水平・垂直揃えを検証するレポートを生成。
- `generate_text_anchors.py`: 絶対座標レイアウトからテキストアンカー定義を生成。

## 実行例

```bash
# 罫線レイアウトを更新
python tools/extract_lines.py

# フォントメトリクスのレポートを作成
python tools/font_metrics_report.py

# 空の罫線PDFを生成してサイズを確認
python tools/generate_blank_resume.py
python tools/verify_pdf.py
```
