# 開発者ガイド

このドキュメントは、jtr-generatorのローカル開発環境のセットアップ、開発タスク、コーディング規約を説明します。

## セットアップ

### 必要要件

- Python 3.11以上
- [uv](https://github.com/astral-sh/uv) 0.5.0以上

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/unagi/jtr-generator.git
cd jtr-generator

# 依存パッケージのインストール
uv sync --all-extras --dev

# フォントのセットアップ（オプション）
# デフォルトでskill/assets/fonts/BIZ_UDMincho/が使用されます
```

## ディレクトリ構成

```
jtr-generator/
├── README.md                   # プロジェクト概要
├── AGENTS.md                   # AIエージェント向け技術仕様
├── CLAUDE.md                   # Agent Skills技術仕様
├── DEVELOPMENT.md              # このファイル（開発者向けガイド）
├── pyproject.toml              # Pythonプロジェクト設定
├── skill/                      # Agent Skillsパッケージ
│   ├── SKILL.md                # LLM向け指示
│   ├── README.md               # エンドユーザー向けガイド
│   ├── assets/                 # データ/フォント/スキーマ
│   │   ├── config.yaml         # 設定テンプレート
│   │   ├── data/               # レイアウトデータ（A4）
│   │   ├── examples/           # サンプルデータ
│   │   ├── fonts/              # デフォルトフォント
│   │   └── schemas/            # JSON Schema
│   ├── references/             # エンドユーザー向けドキュメント
│   └── scripts/                # 実装本体
│       ├── main.py             # Skillエントリーポイント
│       └── jtr/                # 共通実装（PDF生成・データ処理）
├── tests/                      # テストコード
│   ├── scripts/                # エントリーポイント・共通実装のテスト
│   ├── generators/             # PDF生成テスト
│   └── fixtures/               # テストデータ
├── tools/                      # 開発ツール
│   ├── extract_lines.py        # 罫線抽出ツール
│   └── layout/                 # レイアウト検証ツール
├── docs/                       # 開発ドキュメント
├── outputs/                    # 一時出力（.gitignore対象）
└── build/                      # ビルド成果物（.gitignore対象）
```

## 開発タスク

### テスト実行

```bash
# 全テスト実行（カバレッジ付き）
uv run poe test-cov

# 視覚的テスト（ピクセル差異 + SSIM）
uv run pytest tests/generators/test_pdf_visual.py -v

# 特定のテストのみ実行
uv run pytest tests/scripts/test_main.py -v
```

### コード品質チェック

```bash
# Lint（Ruff）
uv run poe lint

# フォーマットチェック
uv run poe format-check

# 型チェック（mypy）
uv run poe typecheck

# 全チェック一括実行（推奨）
uv run poe check-all
```

**重要**: コミット前に必ず`uv run poe check-all`を実行してください。CI/CDで同じチェックが実行されます。

### Agent Skillsパッケージのビルド

```bash
# jtr-generator.zip を生成
uv run poe build-skill

# 成果物: build/jtr-generator.zip
```

### レイアウト検証ツール

```bash
# 固定ラベルの配置検証
uv run python tools/layout/analyze_text_alignment.py

# データフィールドの配置検証
uv run python tools/layout/analyze_data_field_alignment.py
```

## コーディング規約

### Python固有（Ruff + Mypy）

- **行長**: 100文字以内
- **型ヒント**: 必須（`mypy strict mode`）
- **例外処理**: `# type: ignore`, `# noqa`は最小限にし、必要な場合は理由をコメント
- **未使用コード**: 未使用import、変数は削除
- **命名規則**: PEP 8準拠

### レイアウト単位（グラウンドルール）

- **フォントサイズおよびフォントに直接影響する余白/行間**: ptで設定
- **罫線や図形、用紙全体のレイアウト**: mmで設定

### テスト要件

- **新規/変更機能**: 必ずテストを追加
- **カバレッジ**: 80%以上を維持
- **テストマーカー**: `pytest --strict-markers`準拠
- **テストの品質**: 単にカバレッジを稼ぐのではなく、意味のあるテストケースを書く

詳細: [docs/testing.md](docs/testing.md)

### 品質チェック回避の禁止

以下の記述は**原則禁止**です:

```python
# ❌ 禁止例
result = some_func()  # type: ignore
data = get_data()  # noqa: F401
```

やむを得ず使用する場合は、以下の条件を満たす必要があります:

1. **理由を明記**: なぜ必要かをコメントで説明
2. **代替案の検討**: より適切な解決策がないか検討済み
3. **最小範囲**: 必要最小限の範囲にのみ適用

## CI/CD

GitHub Actionsで以下を自動実行:

- **CI**: Lint、フォーマットチェック、型チェック、テスト（カバレッジ測定）
- **Codecov**: カバレッジレポート自動アップロード
- **SonarCloud**: コード品質分析
- **Release**: Agent Skillsパッケージ自動ビルド・リリース

詳細: [.github/workflows/](.github/workflows/)

### 品質ゲート（SonarCloud）

以下の基準を**必ず**満たす必要があります:

- **カバレッジ**: 平均80%以上必須（これを下回るとCIが失敗します）
- **重大度**: 「Critical」「Blocker」の指摘を残さない
- **コード品質**: SonarCloudのQuality Gateをすべて通過

## 品質指標

| 指標 | 目標 | 現在 |
|------|------|------|
| テストカバレッジ | 80%以上 | 82% |
| 視覚品質（SSIM） | > 0.895 | 0.905 |
| ピクセル差異 | < 6.0% | 5.67% |

## デバッグ

### ローカルでのPDF生成

```bash
# 履歴書のみ
uv run python skill/scripts/main.py rirekisho \
  skill/assets/examples/sample_rirekisho.yaml \
  --output outputs/rirekisho.pdf

# 職務経歴書のみ
uv run python skill/scripts/main.py career_sheet \
  skill/assets/examples/sample_rirekisho.yaml \
  skill/assets/examples/sample_career_content.md \
  --output outputs/career_sheet.pdf

# 両方まとめて
uv run python skill/scripts/main.py both \
  skill/assets/examples/sample_rirekisho.yaml \
  skill/assets/examples/sample_career_content.md \
  --output-dir outputs
```

### Python APIの使用

```python
from pathlib import Path
from skill.scripts.main import main

# 履歴書のみ
output = main(
    input_data=Path("skill/assets/examples/sample_rirekisho.yaml"),
    document_type="rirekisho",
    output_path=Path("outputs/rirekisho.pdf"),
)

# 職務経歴書のみ
output = main(
    input_data=Path("skill/assets/examples/sample_rirekisho.yaml"),
    document_type="career_sheet",
    markdown_content=Path("skill/assets/examples/sample_career_content.md"),
    output_path=Path("outputs/career_sheet.pdf"),
)

# 両方まとめて
outputs = main(
    input_data=Path("skill/assets/examples/sample_rirekisho.yaml"),
    document_type="both",
    markdown_content=Path("skill/assets/examples/sample_career_content.md"),
    output_path=Path("outputs"),
)
```

## トラブルシューティング

### テストが失敗する

1. **依存関係の確認**: `uv sync --all-extras --dev`を再実行
2. **カバレッジ不足**: 新規コードにテストを追加
3. **視覚テストの失敗**: 期待されるレイアウトと実際の出力を比較

### Lintエラー

1. **自動修正**: `uv run poe format`で自動修正
2. **手動修正**: Ruffの指摘に従って修正
3. **型エラー**: 型ヒントを追加

### ビルドが失敗する

1. **ファイルの確認**: `skill/`配下の必須ファイルが揃っているか確認
2. **権限の確認**: `build/`ディレクトリの書き込み権限を確認

## リリースフロー

1. **機能追加/バグ修正**: ブランチを作成
2. **テスト**: `uv run poe check-all`で全チェック通過
3. **PR作成**: mainブランチへのPR
4. **マージ**: PRマージ後、mainブランチに反映
5. **タグ作成**: `git tag vX.X.X && git push origin vX.X.X`
6. **リリース**: GitHub Actionsが自動的にzipを生成・リリース

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずIssueで議論してください。

## その他のドキュメント

- **プロジェクト全体仕様**: [AGENTS.md](AGENTS.md)
- **Agent Skills技術仕様**: [CLAUDE.md](CLAUDE.md)
- **エンドユーザー向けマニュアル**: [skill/README.md](skill/README.md)
- **テスト仕様**: [docs/testing.md](docs/testing.md)
