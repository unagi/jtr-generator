# jtr-generator

[![CI](https://github.com/unagi/jtr-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/unagi/jtr-generator/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/unagi/jtr-generator/branch/main/graph/badge.svg)](https://codecov.io/gh/unagi/jtr-generator)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=unagi_jtr-generator&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=unagi_jtr-generator)

JIS規格準拠の日本の履歴書（rirekisho）をPDF形式で生成する**Agent Skills / Codex対応ツール**です。

## プロジェクト概要

このプロジェクトは、Claude Agent Skills（Claude.ai）およびCodex（MCP経由）で動作する履歴書生成Skillです。
対話的な情報収集、またはYAML/JSONファイルから、JIS規格に準拠した日本の履歴書PDFを生成できます。

**主な特徴:**
- JIS規格準拠の精密なレイアウト（208本の罫線、33個の固定ラベル）
- A4サイズ2ページ構成
- 西暦/和暦の切り替え
- カスタムフォント対応
- JSON Schema準拠のデータバリデーション

## ドキュメント

### エンドユーザー向け
- **[skill/README.md](skill/README.md)** - Skill使用方法（Claude.ai/Codexでの使い方）
- **[サンプルデータ](skill/examples/)** - [YAML](skill/examples/sample_resume.yaml) | [PDF](skill/examples/sample_resume.pdf)

### 開発者向け
- **[AGENTS.md](AGENTS.md)** - プロジェクト全体仕様（LLM非依存の設計ドキュメント）
- **[CLAUDE.md](CLAUDE.md)** - Agent Skills技術仕様（Beta API、Files API）
- **[skill/SKILL.md](skill/SKILL.md)** - LLM向け指示（YAML Frontmatter形式）

### 開発履歴
- **[docs/development/layout_adjustment_history.md](docs/development/layout_adjustment_history.md)** - レイアウト調整履歴
- **[docs/development/font_selection_rationale.md](docs/development/font_selection_rationale.md)** - フォント選定の根拠

## ディレクトリ構成

```
jtr-generator/
├── README.md                   # このファイル（開発者向けプロジェクト説明）
├── AGENTS.md                   # プロジェクト全体仕様
├── CLAUDE.md                   # Agent Skills技術仕様
├── pyproject.toml              # Pythonプロジェクト設定
├── skill/                      # Agent Skillsパッケージ
│   ├── README.md               # エンドユーザー向けマニュアル
│   ├── SKILL.md                # LLM向け指示
│   ├── main.py                 # エントリーポイント
│   ├── config.yaml             # ユーザー設定テンプレート
│   ├── jtr/                    # 共通実装
│   │   ├── pdf_generator.py   # PDF生成ロジック
│   │   ├── resume_data.py     # データ読み込み・検証
│   │   ├── japanese_era.py    # 和暦変換
│   │   └── layout/             # レイアウト計算
│   ├── data/                   # レイアウトデータ
│   │   └── a4/
│   │       ├── resume_layout.json
│   │       ├── definitions/
│   │       │   └── manual_bounds.json
│   │       └── rules/
│   │           ├── label_alignment.json
│   │           └── field_alignment.json
│   ├── schemas/                # JSON Schema
│   │   ├── resume_schema.json
│   │   └── layout_schema.json
│   ├── examples/               # サンプルデータ
│   └── fonts/                  # デフォルトフォント
├── tests/                      # テストコード
│   ├── jtr/                    # ユニットテスト
│   ├── generators/             # PDF生成テスト
│   └── fixtures/               # テストデータ
├── tools/                      # 開発ツール
│   ├── build_skill.py          # Agent Skillsパッケージビルド
│   ├── extract_lines.py        # 罫線抽出ツール
│   └── layout/                 # レイアウト検証ツール
├── docs/                       # 開発ドキュメント
│   └── development/
├── outputs/                    # 一時出力（.gitignore対象）
└── build/                      # ビルド成果物（.gitignore対象）
```

## セットアップ（開発環境）

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
# デフォルトでskill/fonts/BIZ_UDMincho/が使用されます
```

## 開発タスク

### テスト実行

```bash
# 全テスト実行（カバレッジ付き）
uv run poe test-cov

# 視覚的テスト（ピクセル差異 + SSIM）
uv run pytest tests/generators/test_pdf_visual.py -v
```

### コード品質チェック

```bash
# Lint（Ruff）
uv run poe lint

# フォーマットチェック
uv run poe format-check

# 型チェック（mypy）
uv run poe typecheck

# 全チェック一括実行
uv run poe check-all
```

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

## CI/CD

GitHub Actionsで以下を自動実行:

- **CI**: Lint、フォーマットチェック、型チェック、テスト（カバレッジ測定）
- **Codecov**: カバレッジレポート自動アップロード
- **SonarCloud**: コード品質分析
- **Release**: Agent Skillsパッケージ自動ビルド・リリース

詳細: [.github/workflows/](.github/workflows/)

## 品質指標

| 指標 | 目標 | 現在 |
|------|------|------|
| テストカバレッジ | 80%以上 | 82% |
| 視覚品質（SSIM） | > 0.895 | 0.905 |
| ピクセル差異 | < 6.0% | 5.67% |

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずIssueで議論してください。

## リンク

- **プロジェクト全体仕様**: [AGENTS.md](AGENTS.md)
- **Agent Skills技術仕様**: [CLAUDE.md](CLAUDE.md)
- **エンドユーザー向けマニュアル**: [skill/README.md](skill/README.md)
