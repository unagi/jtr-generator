# jtr-generator - 日本の履歴書生成Skill

[![CI](https://github.com/unagi/jtr-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/unagi/jtr-generator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/unagi/jtr-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/unagi/jtr-generator)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=unagi_jtr-generator&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=unagi_jtr-generator)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 概要

Claude SkillsでJIS規格準拠の日本の履歴書を自動生成するカスタムSkillです。
ユーザーはClaude.aiで自然言語で依頼するだけで、PDF形式の履歴書が生成されます。
データはYAML/JSON形式でバックアップ・編集・再利用できます。

## このSkillができること

- 📄 JIS規格準拠の日本の履歴書レイアウト生成
- 📑 PDF形式（.pdf）での出力（印刷・提出用）
- 💾 構造化データ（YAML/JSON）での入出力（バックアップ・リストア）
- 🎨 あなたの好きな日本語フォントでの出力

## インストール方法

### Claude Skills（対応済み）

#### 前提条件

- Claude.aiアカウント（https://claude.ai）
- Webブラウザ

#### Skillのアップロード手順

1. **Skillパッケージのダウンロード**
   - このリポジトリから最新リリースをダウンロード
   - `jtr-generator-skill.zip`を任意のフォルダに保存

2. **パッケージの展開**
   ```bash
   unzip jtr-generator-skill.zip -d jtr-generator-skill
   cd jtr-generator-skill
   ```

3. **日本語フォントの設定（オプション）**

   **v0.1.0以降、デフォルトフォント（BIZ UDMincho）が同梱されています。**
   フォント設定をスキップした場合、デフォルトフォントが自動的に使用されます。

   **カスタムフォントを使用する場合:**

   a. お好みの日本語フォントファイル（.ttf または .otf）を用意
      - 例: IPAexフォント、Notoフォント、源ノ角ゴシック等
      - **商用利用可能なフリーフォントを推奨**

   b. フォントファイルを`fonts/`ディレクトリに配置
      ```bash
      mkdir -p fonts/custom
      cp /path/to/your/font.ttf fonts/custom/
      ```

   c. 設定ファイル`config.yaml`を編集
      ```yaml
      fonts:
        main: fonts/custom/your-font.ttf        # 本文用フォント
        heading: fonts/custom/your-font-bold.ttf # 見出し用フォント（オプション）
      ```

   **デフォルトフォント（BIZ UDMincho）について:**
   - 設定なしでもBIZ UDMinchoが自動的に使用されます
   - より好みに合ったフォントを使用したい場合のみカスタム設定を行ってください

4. **パッケージの再圧縮**
   ```bash
   cd ..
   zip -r jtr-generator-skill-custom.zip jtr-generator-skill/
   ```

5. **Claude.aiでアップロード**
   - https://claude.ai にログイン
   - 画面右上の設定アイコンをクリック
   - **Settings** → **Features** → **Custom Skills** に移動
   - **Upload Skill** ボタンをクリック
   - 作成した `jtr-generator-skill-custom.zip` を選択
   - アップロード完了を確認

6. **動作確認**
   - 新しいチャットを開始
   - 「履歴書を作成できますか？」と入力
   - Skillが認識されることを確認

### ChatGPT（未対応）

現在、OpenAIはカスタムスキルのアップロード機能を提供していません。
OpenAIがSkills相当の機能を提供次第、対応を検討します。

**代替案の検討中:**
- GPTs機能の活用
- Code Interpreter + テンプレートファイル
- プラグイン開発

### Gemini（未対応）

現在、Googleはカスタムスキルのアップロード機能を提供していません。
GeminiがSkills相当の機能を提供次第、対応を検討します。

**代替案の検討中:**
- Google Apps Script連携
- Google Sheets API経由での生成

## 使い方

### 基本的な依頼方法

Claude.aiのチャットで以下のいずれかの方法で依頼してください。

#### 方法1: チャット内のテキストから生成

必要な情報をチャット内で提供します。不足項目がある場合、Skillが対話的に質問します。

**例:**
```
履歴書を作成してください。

【基本情報】
氏名: 山田太郎（やまだたろう）
生年月日: 1990年4月1日
性別: 男性
現住所: 東京都渋谷区神南1-1-1
電話: 03-1234-5678
携帯: 090-1234-5678
メール: yamada@example.com

【学歴】
2006年3月 東京都立〇〇高等学校 卒業
2010年3月 〇〇大学 工学部 情報工学科 卒業

【職歴】
2010年4月 株式会社〇〇 入社
2015年3月 同社 退職（一身上の都合により）
2015年4月 株式会社△△ 入社
現在に至る

【資格】
2012年10月 基本情報技術者試験 合格
2014年6月 応用情報技術者試験 合格
```

**不足項目がある場合:**

Skillが自動的に不足情報を質問します。

```
あなた: 履歴書を作成してください。氏名は山田太郎です。

Skill: 承知しました。以下の情報を教えてください：
- 生年月日
- 現住所
- 連絡先（電話番号、メールアドレス）
- 学歴
- 職歴
...
```

#### 方法2: 構造化データファイルから生成

YAML または JSON ファイルをアップロードして生成します。

**例（YAMLファイル）:**
```
[ファイルを添付: my_resume.yaml]

このYAMLファイルから履歴書を生成してください。
```

**例（JSONファイル）:**
```
[ファイルを添付: my_resume.json]

このJSONデータから履歴書を生成してください。
```

### 出力フォーマット

**履歴書PDF:**

常にPDF形式で出力されます。フォーマット指定は不要です。

```
履歴書を作成してください。
→ PDF形式の履歴書が生成されます
```

**データのバックアップ（エクスポート）:**

履歴書データをYAML/JSON形式でエクスポートできます。編集・再利用が可能です。

```
# YAML形式でエクスポート
履歴書データをYAML形式でエクスポートしてください。

# JSON形式でエクスポート
履歴書データをJSON形式でエクスポートしてください。
```

### オプション指定

指定がない場合は既定値が使用されます。

| オプション | 既定値 | セッション内での変更 | 恒久的な変更（config.yaml） |
|-----------|--------|-------------------|---------------------------|
| **和暦/西暦** | 西暦 | 「和暦で表記してください」<br>「西暦で統一してください」 | `options:`<br>`  date_format: wareki` |
| **用紙サイズ** | A4 | 「B5サイズで作成してください」<br>「A4サイズに戻してください」 | `options:`<br>`  paper_size: B5` |

### データフォーマット

構造化データは **YAML形式** または **JSON形式** で提供できます。
すべてのデータは `schemas/resume_schema.json` で定義されたJSON Schemaに準拠します。

#### データ構造の概要

```yaml
personal_info:      # 基本情報（氏名、生年月日、連絡先等）
education:          # 学歴（配列）
work_history:       # 職歴（配列）
qualifications:     # 資格・免許（配列）
additional_info:    # 志望動機・自己PR
```

#### サンプルファイル

完全なデータ例は以下のファイルを参照してください:

- **YAML形式**: [examples/sample_resume.yaml](examples/sample_resume.yaml)
- **JSON形式**: [examples/sample_resume.json](examples/sample_resume.json)

#### データ仕様

- **スキーマ定義**: `schemas/resume_schema.json` で公開
- **バリデーション**: YAMLは処理前にJSON化され、JSON Schemaと突合
- **マルチライン**: YAMLは `|` 記法で改行を保持、JSONは `\n` エスケープ

## 動作例

### 例1: 対話的に情報を入力して生成

**入力:**
```
履歴書を作成してください。
氏名: 佐藤花子
生年月日: 1995年7月15日
```

**動作:**
1. Skillが不足情報を質問
   ```
   以下の情報を教えてください：
   - 氏名のふりがな
   - 現住所
   - 連絡先（電話番号、メールアドレス）
   - 学歴
   - 職歴
   ```
2. ユーザーが順次回答
3. すべての必須項目が揃ったらPDF生成

**出力:**
- `rirekisho_satou_hanako.pdf`

### 例2: チャット内のテキストから生成

**入力:**
```
以下の情報で履歴書を作成してください。

氏名: 田中一郎（たなかいちろう）
生年月日: 1988年12月3日
現住所: 大阪府大阪市北区梅田1-1-1
電話: 06-1234-5678
メール: tanaka@example.com

学歴:
2004年3月 大阪府立〇〇高等学校 卒業
2008年3月 〇〇大学 経済学部 経済学科 卒業

職歴:
2008年4月 〇〇株式会社 入社
2013年6月 同社 営業部 主任
2018年3月 同社 退職
2018年4月 株式会社△△ 入社、現在に至る

資格:
2010年11月 日商簿記検定2級 合格
2015年3月 TOEIC 850点取得
```

**出力:**
- `rirekisho_tanaka_ichirou.pdf`

### 例3: YAMLファイルから生成

**入力:**
```
[ファイルを添付: my_resume.yaml]

このYAMLファイルから履歴書を生成してください。
```

**出力:**
- `rirekisho_yamada_tarou.pdf`

### 例4: データのバックアップ

**入力:**
```
履歴書データをYAML形式でエクスポートしてください。
```

**出力:**
- `resume_backup.yaml` - 編集・再利用可能な構造化データ

**用途:**
- 別のPCで履歴書を作成する際に再利用
- テキストエディタで直接編集
- バージョン管理（Git等）

## 制限事項

### 現在の制限

- **証明写真の埋め込み**: 画像パスの指定のみ対応（自動埋め込みは将来対応予定）
- **複雑な職歴**: 転職回数が10回を超える場合、レイアウトが崩れる可能性
- **カスタムレイアウト**: 現在は標準的なJIS規格フォーマットのみ対応

### プラットフォーム制限

- **個人利用限定**: Claude.aiにアップロードしたSkillは個人アカウント内でのみ利用可能
- **生成時間**: 1-2分程度かかります（Claude Skills APIの仕様）
- **ファイルサイズ**: 生成ファイルは通常1MB以下

## トラブルシューティング

### Skillが認識されない

**症状**: 「履歴書を作成してください」と依頼してもSkillが実行されない

**対処法**:
1. Settings → Features → Custom Skills でSkillがアップロードされているか確認
2. 「日本の履歴書」「JIS規格の履歴書」など、より具体的に依頼
3. Skillを一度削除して再アップロード

### 生成に失敗する

**症状**: エラーメッセージが表示される

**対処法**:
1. 入力データのフォーマットを確認（特に日付形式）
2. 必須項目（氏名、生年月日）が含まれているか確認
3. JSONファイルの場合、文法エラーがないか確認

### レイアウトが崩れる

**症状**: 生成されたファイルのレイアウトが期待と異なる

**対処法**:
1. 職歴・学歴の件数を減らす
2. 長いテキスト（志望動機等）を200-300文字程度に収める
3. 用紙サイズ（A4/B5）を明示的に指定

### ファイルがダウンロードできない

**症状**: 生成完了後、ファイルのダウンロードリンクが表示されない

**対処法**:
1. 1-2分待つ（生成には時間がかかります）
2. ブラウザをリロード
3. 別のブラウザで試す

### フォントが正しく表示されない

**症状**: 生成されたPDFのフォントが期待と異なる、文字化けする

**対処法**:
1. `config.yaml`でフォントパスが正しく設定されているか確認
2. フォントファイル（.ttf/.otf）が`fonts/`ディレクトリに存在するか確認
3. フォントファイルが破損していないか確認（別のアプリで開いてみる）
4. Skillパッケージを再圧縮し、再アップロード

## よくある質問

**Q: Claude.ai以外で使えますか？**
A: 現在は個人利用を想定しており、Claude.aiでの使用を推奨しています。開発者向けにはClaude APIやClaude Code経由での利用も可能です（詳細は[DEVELOPMENT.md](DEVELOPMENT.md)参照）。

**Q: ChatGPTやGeminiでも使えるようになりますか？**
A: OpenAI/GoogleがSkills相当の機能を提供次第、対応を検討します。現時点では技術的に実現できません。

**Q: 生成された履歴書は編集できますか？**
A: PDFは編集できませんが、YAML/JSON形式でデータをエクスポートし、修正後に再生成することで内容を変更できます。

**Q: 証明写真を自動で配置できますか？**
A: 現在は証明写真エリアのみ用意され、画像の自動埋め込みは未対応です。PDF生成後、PDF編集ツールで手動で画像を挿入してください。

**Q: 生成にどのくらい時間がかかりますか？**
A: 通常1-2分程度です。これはClaude Skills APIの仕様であり、正常な動作です。

**Q: 職務経歴書も作成できますか？**
A: 現在は履歴書のみ対応しています。職務経歴書対応は将来のロードマップに含まれています。

**Q: データは安全ですか？**
A: 入力データはClaudeのセキュアな実行環境内でのみ処理され、生成後は保持されません。詳細はAnthropicのプライバシーポリシーを参照してください。

**Q: 商用利用できますか？**
A: このSkillはMITライセンスで提供されており、商用利用可能です。ただしClaude APIの利用規約に従ってください。

**Q: なぜフォントが同梱されていないのですか？**
A: 多くの日本語フォントはライセンス上、再配布が禁止されています。そのため、ユーザー自身がフォントを用意し設定する方式を採用しています。これにより、あなたの好きなフォントで履歴書を作成できます。

**Q: どのフォントを使えば良いですか？**
A: 商用利用可能なフリーフォントを推奨します。例: IPAexフォント、Noto Sans JP、源ノ角ゴシック、BIZ UDゴシック等。フォントのライセンスを必ず確認してください。

**Q: フォントを設定しなくても使えますか？**
A: はい、使えます。デフォルトのシステムフォントが使用されますが、環境によっては見た目が変わる可能性があります。より良い見た目のため、フォント設定を推奨します。

## 開発者向け情報

このプロジェクトの開発に参加する場合は、以下のドキュメントを参照してください:

- [DEVELOPMENT.md](DEVELOPMENT.md) - ローカル開発・テスト・デバッグ方法
- [AGENTS.md](AGENTS.md) - プロジェクト全体仕様・ドメイン知識
- [CLAUDE.md](CLAUDE.md) - Claude Skills API技術詳細

## 参考情報

### 日本語フォント

履歴書作成に使用できる商用利用可能な日本語フォントの配布サイト:

- [IPAフォント](https://moji.or.jp/ipafont/) - 独立行政法人情報処理推進機構が提供する高品質フォント
- [Google Fonts - Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP) - Googleが提供する多言語対応フォント
- [源ノ角ゴシック (Source Han Sans)](https://github.com/adobe-fonts/source-han-sans) - Adobe提供のオープンソースフォント
- [BIZ UDゴシック/明朝](https://github.com/googlefonts/morisawa-biz-ud-gothic) - モリサワ提供のユニバーサルデザインフォント

各フォントのライセンス条項を必ず確認してから使用してください。

## ライセンス

### プロジェクトライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) を参照してください。

### 同梱フォント

#### BIZ UDMincho

このプロジェクトには、モリサワ提供の BIZ UDMincho フォントがデフォルトフォントとして同梱されています。

- **フォント名**: BIZ UDMincho Regular
- **提供元**: Morisawa Inc.
- **ライセンス**: SIL Open Font License, Version 1.1
- **プロジェクトURL**: https://github.com/googlefonts/morisawa-biz-ud-mincho

BIZ UDMincho は SIL Open Font License 1.1 の下で配布されており、商用利用・再配布が可能です。
ライセンス全文は [fonts/BIZ_UDMincho/OFL.txt](fonts/BIZ_UDMincho/OFL.txt) を参照してください。

**著作権表示:**
```
Copyright 2022 The BIZ UDMincho Project Authors
(https://github.com/googlefonts/morisawa-biz-ud-mincho)
```
