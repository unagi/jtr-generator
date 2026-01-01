---
name: jtr-generator
description: 履歴書はJIS規格準拠、職務経歴書は一般的体裁の日本のレジュメをPDF生成するSkill。対話的な情報収集またはYAML/JSONファイルからPDF生成が可能。
---

# 日本のレジュメ（履歴書・職務経歴書）生成Skill

このスキルは[Agent Skills仕様](https://agentskills.io)に準拠しています。

## Overview

履歴書はJIS規格準拠、職務経歴書は日本国内の一般的体裁でPDFを生成します。

**主な機能:**
- 対話（呼び出し側LLM）による情報収集、またはYAML/JSONからの一括生成
- 履歴書（JIS様式準拠）と職務経歴書（一般的体裁/Markdown本文）に対応
- 和暦/西暦の切り替え
- フォント選択（明朝/ゴシック）

## Details

本ドキュメント（SKILL.md）が置かれたディレクトリをスキルルートとし、以降のパスはすべてそのルートからの相対パスとする。

### 入力
- 履歴書データ: YAML/JSON（`assets/schemas/rirekisho_schema.json` に準拠）
- 職務経歴書本文: Markdown（文字列またはファイル）
  - examplesとschemaが一致していることが最優先

### 職務経歴書の構成とMarkdownの責務
- プロフィール/免許・資格は履歴書データから出力
- それ以降（職務要約、職務経歴、自己PRなど）はMarkdown本文で記述
- MarkdownはGitHub Flavored Markdownに準拠し、H2（`##`）を起点に構成する
- SNS/個人サイト、登壇・執筆はMarkdown本文に記載（複数可）
- 規約から逸脱する場合は出力品質を保証しない

### 出力
- PDF（A4）
- APIは `document_type`（`rirekisho` / `career_sheet` / `both`）、CLIは `rirekisho` / `career_sheet` / `both`
- `both` は `--output-dir` 配下に以下の規則で2ファイルを出力する（`rirekisho_YYMMDD-HHMMSS.pdf` / `career_sheet_YYMMDD-HHMMSS.pdf`）
  - `YYMMDD-HHMMSS` はUTC（24時間表記）を用いる
- 入力に使ったYAML/Markdownはバックアップとしてそのまま再利用できる

### オプション
- `date_format`: `seireki`（既定値） / `wareki`
- `paper_size`: `A4`（B5は将来対応）
- `font`: `mincho` / `gothic`（履歴書・職務経歴書で共通）

### カスタマイズ（assets/config.yaml）
設定ファイル（`assets/config.yaml`）でフォント（`fonts.mincho` / `fonts.gothic`）や色（`styles.colors`）を変更できます。  
設定を更新するにはSkillの再アップロードが必要なので、その前提を明示して案内してください。

### エントリーポイント
- CLI: `scripts/main.py`
- Python API: `scripts/main.py` の `main()`
  - 戻り値は単体生成で `Path`、`both` で `list[Path]`

## References

- ユーザー向け案内: `references/README.md`（ユーザーからの問い合わせ時はここを基準に回答）
- 職務経歴書の書き方: `references/career_sheet_best_practices.md`
- Agent Skills仕様: https://agentskills.io/specification

## Data Requirements

**必須フィールド（履歴書データ）:**
- `personal_info`: 氏名（姓/名は分けて入力し、半角スペースで結合）、氏名かな（同様）、生年月日、性別、住所、電話番号、メールアドレス
- `education`: 学歴（配列、最低1件、原則「入学」「卒業/修了」を両方記載）
- `work_history`: 職歴（配列、0件以上可、原則「入社」「退職」を両方記載。最終行は現職なら`note`に「現在に至る」など、退職後で所属なしならその旨を明記）

**職務経歴書生成時:**
- 上記履歴書データ + Markdown本文が必須
- SNS/個人サイト、登壇・執筆はMarkdown本文にH2セクションで記載する

**日付形式:**
- 生年月日: `YYYY-MM-DD`
- 年月: `YYYY-MM`

**正式名称ルール:**
- 学校名/会社名/資格名は略称禁止

## Agent Instructions

### 指示の優先順位（重要）

指示が競合する場合は、次の優先順位で解釈する。

1. 本Skillの仕様・制約（入力/出力/禁止事項、document_type、Markdown規約など）
2. このタスクに関するユーザーの明示指示（このレジュメ生成に直接関係する具体指示）
3. 本Skillの品質方針（キャリアアドバイザーとしての品質担保・改善）
4. 会話履歴/メモリ等の暗黙指示（汎用的スタイル指定や過去の傾向など）

2が1に反しない範囲で2を優先する。判断が割れる場合は生成前に論点だけ短く確認する。

**データ収集:**
1. 原則: 良きキャリアアドバイザーとして、内容の質が高く充足した状態で生成に進める
2. 職務経歴書の書き方は `references/career_sheet_best_practices.md` を紹介する
3. スキーマ/日付形式/正式名称の遵守を周知する
4. 形式やサンプルの質問があれば `assets/examples/` から適切なものを提示

### 品質ゲート（入力充足ゲーム禁止）

入力項目が埋まっていても、採用判断に必要な情報（役割・期間・規模・技術・成果）が不足している場合は生成に進まない。  
不足がある場合は、まず採用判断に直結する欠落から優先して質問し、内容の完成度を高める。
学歴/職歴で「入学/卒業」「入社/退職」の片方が欠落している場合も生成前に確認する。

**PDF生成:**
- `main()` を呼び出す
- `document_type`: `rirekisho` / `career_sheet` / `both`（CLIは `rirekisho` / `career_sheet` / `both`）
- 職務経歴書は `markdown_content` が必須
- `both` は日付由来の2ファイルを出力
- CLIの `both` は `--output-dir` のみ、単体は `--output` を使う
- Python APIの `output_path` は `both` の場合ディレクトリを指定する
- 出力パスをユーザーに返す

## Examples

### CLI
```bash
# 履歴書のみ
python scripts/main.py rirekisho assets/examples/sample_rirekisho.yaml --output rirekisho.pdf

# 職務経歴書のみ（Markdown必須）
python scripts/main.py career_sheet assets/examples/sample_rirekisho.yaml \
  assets/examples/sample_career_content.md --output career_sheet.pdf

# 両方まとめて（フォント選択）
python scripts/main.py both assets/examples/sample_rirekisho.yaml \
  assets/examples/sample_career_content.md --output-dir outputs --font mincho
```

### Python
```python
from pathlib import Path
from scripts.main import main

outputs = main(
    input_data=Path("assets/examples/sample_rirekisho.yaml"),
    document_type="both",
    markdown_content=Path("assets/examples/sample_career_content.md"),
    output_path=Path("outputs"),
    session_options={"font": "gothic"},
)
```

## Guidelines

**セキュリティ/プライバシー:**
- 個人情報の取り扱いに注意
- エラーは日本語で明確に提示

## Non-goals / Prohibited Usage

- スキーマ外フィールドの投入で挙動を変えようとする
- 型違い/必須欠落/日付フォーマット違反を許容して動かそうとする
- `both` の出力先をファイルパスにするなど、引数の想定外運用
- Markdown規約（H2起点/GFM）違反を前提に自動補正させようとする

### 推測・補完の取り扱い（重要）

- ユーザーが提示していない事実・数値を断言して記載しない（捏造禁止）
- 推測/補完を行う場合は、(a) 根拠（会話履歴 / 一般的な変換規則 等）を明示し、(b) 生成前にユーザー確認を取る
- ユーザー確認が取れない場合は、推測箇所を「要確認」として残すか、空欄にする
- FAQに定義する「自動でよい整形」は確認不要。それ以外は生成前に確認する

## FAQ / Troubleshooting

**バリデーションはどこまで行う？**  
必須項目・型・日付形式の一部をチェックするが、網羅的な検証は保証しない。呼び出し側はスキーマ準拠の入力を作成すること。

**`date_format` はMarkdown本文も変換する？**  
履歴書データと履歴書由来セクションのみが対象。Markdown本文の数値は変換しない。

**生成されたPDFは自動削除される？**  
実行環境に依存し、保証しない（ベストエフォート）。

**`main()` の戻り値と順序は？**  
単体生成は `Path`、`both` は `list[Path]`。順序は `[rirekisho, career_sheet]`。

**`both` で同名ファイルが存在する場合は？**  
通常は時刻付き命名で衝突しない。万一同名が存在する場合は上書きする。

**返却される `Path` の基準は？**  
`output_path` に渡したディレクトリ配下のパスを返す。相対/絶対は `output_path` に従う。

**`YYMMDD-HHMMSS` の時刻はどの基準？**  
UTC（24時間表記）。

**履歴書JIS様式の根拠は？**  
厚生労働省の履歴書様式例に基づいています。JIS規格の解説から様式例が削除された後、代替として広く用いられているためです。

**確認が必要な補完 / 自動でよい整形**  
- 自動で行ってよい整形: 表記ゆれ統一（全角/半角、箇条書き体裁、敬体/常体の統一など）
- 生成前に確認が必要: 数値の補完、成果の断言、応募企業向けの主張の具体内容、事実関係が変わりうる記載
