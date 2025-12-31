# tools

レイアウト検証から手動テストスクリプトまで、リポジトリ全体で利用する開発補助ツールをまとめています。生成コード本体とは分離し、ワークスペースの汚染を避けるための置き場として利用します。

## 主なユーティリティ

- `generate_blank_resume.py`: 現在のレイアウトから罫線のみのPDFを生成します。
- `verify_pdf.py`: 生成済みPDFのページサイズなど基本情報を表示します。
- `layout/`: テキスト・データフィールドの整合性を検証する各種スクリプト。
- `manual_career_sheet_generation.py`: 職務経歴書PDFをローカルで試すための手動テストスクリプト。

> 上記以外の開発時に必要なスクリプトも、このディレクトリに配置してください。

## 実行例

```bash
python tools/generate_blank_resume.py
python tools/verify_pdf.py
python tools/manual_career_sheet_generation.py
```
