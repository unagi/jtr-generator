# jtr-generator

[![CI](https://github.com/unagi/jtr-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/unagi/jtr-generator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/unagi/jtr-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/unagi/jtr-generator)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=unagi_jtr-generator&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=unagi_jtr-generator)

JIS規格準拠の日本のレジュメ（履歴書・職務経歴書）をPDF形式で生成する**Agent Skills / Codex対応ツール**です。

Claude Agent Skills（Claude.ai）およびCodex（MCP経由）で動作し、対話的な情報収集またはYAML/JSONファイルから、JIS規格に準拠した日本の履歴書/職務経歴書PDFを生成できます。

**主な特徴:**
- JIS規格準拠の精密なレイアウト（208本の罫線、33個の固定ラベル）
- A4サイズ2ページ構成
- 西暦/和暦の切り替え
- 職務経歴書のMarkdown入力対応
- カスタムフォント対応
- JSON Schema準拠のデータバリデーション

## クイックスタート

### エンドユーザー（Claude.ai/Codexで履歴書を作成したい方）

#### Claude.ai（推奨）

1. **zipファイルのダウンロード**
   - [Releases](https://github.com/unagi/jtr-generator/releases)から最新版の`jtr-generator-vX.X.X.zip`をダウンロード

2. **スキルのアップロード**
   - Claude.ai → 設定 → 機能 → スキル
   - 「カスタムスキルを追加」
   - ダウンロードしたzipファイルを選択

3. **使い方**
   - 新しいチャットで「履歴書を作成してください」と話しかける
   - 必要な情報を順番に入力していく

#### Codex（CLI）

1. **zipファイルのダウンロード**
   - [Releases](https://github.com/unagi/jtr-generator/releases)から最新版をダウンロード

2. **配置**
   ```bash
   # Codexのスキルディレクトリに配置
   mkdir -p ~/.codex/skills
   unzip jtr-generator-vX.X.X.zip -d ~/.codex/skills/jtr-generator
   ```

3. **使い方**
   ```bash
   codex "履歴書を作成してください"
   ```

### 開発者（ローカル開発・コントリビューション）

[DEVELOPMENT.md](DEVELOPMENT.md)を参照してください。

### AIエージェント（技術仕様・実装詳細）

[AGENTS.md](AGENTS.md)を参照してください。

## サンプル

- [YAML入力例](skill/assets/examples/sample_rirekisho.yaml)
- [履歴書PDF](skill/assets/examples/sample_rirekisho.pdf)
- [職務経歴書PDF](skill/assets/examples/sample_career_sheet_mincho.pdf)

## よくある質問

**Q: 生成されたPDFはどこに保存されますか？**
A: Claude.aiでは会話内でダウンロードリンクが表示されます。Codexでは指定したディレクトリに保存されます。

**Q: フォントは変更できますか？**
A: 明朝体とゴシック体から選択できます。会話中に指定するか、`skill/assets/config.yaml`を編集してスキルを再アップロードしてください。

**Q: 和暦と西暦は切り替えられますか？**
A: はい、生成時に指定できます。デフォルトは西暦です。

**Q: サンプルデータはありますか？**
A: 上記「サンプル」セクションを参照してください。

## トラブルシューティング

**エラーが出る場合:**
- 必須項目（氏名、生年月日、学歴、職歴）が入力されているか確認
- 日付形式が`YYYY-MM-DD`（生年月日）または`YYYY-MM`（年月）になっているか確認
- 学校名/会社名/資格名は正式名称で入力（略称禁止）

**生成が途中で止まる場合:**
- 入力データが大きすぎる可能性があります
- 職務経歴書の本文を分割して入力してみてください

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずIssueで議論してください。
