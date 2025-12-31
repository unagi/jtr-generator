# jtr-generator - Agent Skill

JIS規格準拠の日本のレジュメ（履歴書・職務経歴書）をPDF形式で生成するAgent Skillです。

## 概要

このSkillを使用すると、対話的な情報収集またはYAML/JSONファイルから、JIS規格に準拠した日本のレジュメPDFを生成できます。

**対応プラットフォーム:**
- Agent Skills対応のLLMプラットフォーム（Claude.ai、Codex等）
- エントリーポイント: `skill/scripts/main.py`（zip化時はルート直下に展開）

## 使い方

### 1. 対話的生成（履歴書）

LLMに直接情報を伝えて履歴書を作成します。

```
履歴書を作成してください。
氏名は山田太郎です。
生年月日は1990年4月1日です。
```

不足している情報があれば、対話的に質問されます。

### 2. YAMLファイルからの生成（履歴書）

あらかじめ用意したYAMLファイルから履歴書を生成します。

```
[sample_resume.yamlを添付]
このファイルから履歴書を生成してください。
```

### 3. 職務経歴書の生成

履歴書データ（YAML/JSON）とMarkdown本文を渡して職務経歴書を生成します。

```
[sample_resume.yamlを添付]
[sample_career_content.mdを添付]
職務経歴書を作成してください。
```

### 4. 履歴書と職務経歴書のまとめて生成

```
[sample_resume.yamlを添付]
[sample_career_content.mdを添付]
履歴書と職務経歴書をまとめて作成してください。
```

### 5. オプション指定

生成時にオプションを指定できます。

```
和暦表記で履歴書を作成してください。
```

対応オプション:
- **日付フォーマット**: 西暦（デフォルト）/ 和暦
- **用紙サイズ**: A4（デフォルト）/ B5（将来実装予定）

## データ形式

### 必須フィールド

- **personal_info**: 個人情報
  - name: 氏名
  - name_kana: 氏名かな（ひらがな）
  - birthdate: 生年月日（YYYY-MM-DD）
  - gender: 性別（男性/女性/無回答）
  - address: 現住所
  - phone: 電話番号
  - email: メールアドレス

- **education**: 学歴（配列、最低1件）
  - date: 年月（YYYY-MM）
  - type: 入学/卒業/中退
  - school: 学校名（正式名称）
  - department: 学部・学科（オプション）

- **work_history**: 職歴（配列、0件以上）
  - date: 年月（YYYY-MM）
  - type: 入社/退職/異動
  - company: 会社名（正式名称）
  - department: 部署・役職（オプション）
  - note: 備考（オプション）

### オプションフィールド

- **contact_info**: 連絡先（現住所以外に連絡を希望する場合）
- **qualifications**: 資格・免許（配列）
- **additional_info**: 志望動機、自己PR、本人希望欄

### 日付形式

すべての日付は**ISO 8601形式**で指定してください。

- 生年月日: `YYYY-MM-DD`（例: `1990-04-01`）
- 年月: `YYYY-MM`（例: `2010-04`）

### 正式名称の使用

- **学校名**: 「東京都立○○高等学校」（「高校」と略さない）
- **会社名**: 「株式会社○○」または「○○株式会社」（「㈱」禁止）
- **資格名**: 「基本情報技術者試験 合格」（正式名称）

## サンプルデータ

サンプルデータは `assets/examples/sample_resume.yaml` を参照してください。
リポジトリでは `skill/assets/examples/sample_resume.yaml` に配置されています。

```yaml
personal_info:
  name: 山田太郎
  name_kana: やまだたろう
  birthdate: 1990-04-01
  gender: 男性
  postal_code: 150-0041
  address: 東京都渋谷区神南1-1-1
  phone: 03-1234-5678
  mobile: 090-1234-5678
  email: yamada@example.com

education:
  - date: 2006-03
    type: 卒業
    school: 東京都立〇〇高等学校

  - date: 2010-03
    type: 卒業
    school: 〇〇大学
    department: 工学部 情報工学科

work_history:
  - date: 2010-04
    type: 入社
    company: 株式会社〇〇

qualifications:
  - date: 2012-10
    name: 基本情報技術者試験 合格
```

## カスタマイズ

### config.yamlの編集

同梱の `config.yaml` を編集して、デフォルト設定をカスタマイズできます。
リポジトリ内では `skill/assets/config.yaml` にあります。

```yaml
options:
  date_format: seireki  # or wareki
  paper_size: A4        # B5は将来実装予定

styles:
  colors:
    body_text: "#050315"
    main: "#6761af"
    sub: "#cdc69c"
    accent: "#e36162"

fonts:
  main: fonts/custom/your-font.ttf  # カスタムフォント
  career_sheet_main: fonts/custom/your-gothic.ttf  # 職務経歴書用フォント
```

### カスタムフォントの使用

1. `fonts/` ディレクトリにフォントファイル（.ttf または .otf）を配置
2. `config.yaml` の `fonts.main` 設定をコメント解除
3. ファイルパスを指定（相対パスは jtr-generator/ を基準）

## トラブルシューティング

### よくあるエラー

#### 1. 必須フィールド不足

```
エラー: 必須フィールド 'name' が不足しています。
対象: personal_info
skill/assets/examples/sample_resume.yamlを参考にデータを追加してください。
```

**対処法**: 不足しているフィールドを追加してください。

#### 2. 日付形式エラー

```
エラー: フィールド 'personal_info.birthdate' の日付形式が不正です。
期待される形式: YYYY-MM-DD（例: 1990-04-01）
```

**対処法**: 日付をISO 8601形式（YYYY-MM-DD）で指定してください。

#### 3. フォント不在エラー

```
エラー: デフォルトフォントが見つかりません: fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf
BIZ UDMinchoフォントがインストールされているか確認してください。
```

**対処法**: デフォルトフォント（BIZ UDMincho）が正しく配置されているか確認してください。

### ダウンロード

**GitHub Releases（推奨）:**

1. [GitHub Releases](https://github.com/unagi/jtr-generator/releases)から最新版をダウンロード
2. `jtr-generator-vX.X.X.zip` をダウンロード
3. 使用するプラットフォーム（Claude.ai、Codex等）にアップロードまたは配置

**最新版（開発版）:**

[GitHub Actions Artifacts](https://github.com/unagi/jtr-generator/actions)から `jtr-generator-latest.zip` をダウンロード

### ローカル開発・デバッグ

開発者向けのローカルテスト:

```bash
cd /path/to/jtr-generator
python skill/scripts/main.py resume skill/assets/examples/sample_resume.yaml --date-format wareki
```

ビルド:

```bash
uv run poe build-skill
# 成果物: build/jtr-generator.zip
```

## 制約事項

- **用紙サイズ**: 現在はA4のみサポート（B5は将来実装予定）
- **証明写真**: 画像エリアは表示されますが、自動埋め込みは未実装
- **出力先**: カレントディレクトリに `rirekisho.pdf` または `career_sheet.pdf` を生成（`output_path` 指定で変更可）

## ライセンス

MIT License

## 参考資料

- [Agent Skills 公式仕様](https://agentskills.io)
- [GitHub リポジトリ](https://github.com/anthropics/skills)
- [プロジェクトドキュメント](../../README.md)
