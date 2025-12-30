# jtr-generator - エージェント向けガイド

## ⚠️ [IMPORTANT] 最重要: コード品質要件（CI/CD準拠）

<a id="code-quality"></a>

**このセクションは必ず最初に読んでください。CI/CDで失敗しないための必須要件です。**

### 必須チェック（実装後に必ず実行）

実装完了後、**必ず以下のコマンドを実行し、すべて通過することを確認してからコミット**してください。

**推奨: 一括実行**

```bash
# すべてのチェックを一括実行（CI/CDと完全一致）
uv run poe check-all
```

**または個別実行:**

```bash
# Lint（コード品質チェック）
uv run poe lint

# フォーマット検証
uv run poe format-check

# 型チェック（strict mode）
uv run poe typecheck

# テスト + カバレッジ
uv run poe test-cov
```

**これらのチェックはCI/CDで必ず実行されます。ローカルで通過しないコードはCIで失敗します。**

### 品質ゲート（SonarCloud）

以下の基準を**必ず**満たす必要があります:

- **カバレッジ**: **80%以上必須**（これを下回るとCIが失敗します）
- **重大度**: 「Critical」「Blocker」の指摘を残さない
- **コード品質**: SonarCloudのQuality Gateをすべて通過
- **複雑度**: 過度に複雑な関数・クラスを避ける
- **重複**: コードの重複を最小限に

**カバレッジ80%未満の場合、必ずCIで失敗します。新規コード実装時は必ずテストを追加してください。**

### コーディング規約

#### Python固有（Ruff + Mypy）

- **行長**: 100文字以内
- **型ヒント**: 必須（`mypy strict mode`）
- **例外処理**: `# type: ignore`, `# noqa`は最小限にし、必要な場合は理由をコメント
- **未使用コード**: 未使用import、変数は削除
- **命名規則**: PEP 8準拠

#### テスト要件

- **新規/変更機能**: 必ずテストを追加
- **カバレッジ**: 80%以上を維持
- **テストマーカー**: `pytest --strict-markers`準拠
- **テストの品質**: 単にカバレッジを稼ぐのではなく、意味のあるテストケースを書く

**詳細**: [docs/testing.md](docs/testing.md)を参照してください。

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

```python
# ✅ 許容例（理由が明確）
# JSON Schemaでバリデーション済みのため型は保証されている
result = cast(dict, json_data)
```

### CI失敗時の対応フロー

CIが失敗した場合、以下の手順で対処してください:

1. **ローカルで再現**: 失敗したチェックをローカルで実行
   ```bash
   uv run poe lint          # Lintエラーの場合
   uv run poe typecheck     # 型エラーの場合
   uv run poe test-cov      # テスト失敗の場合
   ```

2. **根本原因の特定**:
   - 対症療法（エラーメッセージを消すだけ）ではなく、**なぜ失敗したか**を理解
   - 同じ箇所に2回目の修正が必要になった場合は設計を見直す

3. **修正**:
   - 品質基準を満たすよう修正
   - カバレッジ不足の場合は意味のあるテストを追加

4. **再確認**:
   - **すべての**チェックを再実行してから再プッシュ
   - 一部だけ修正して他のチェックを忘れない

### テストカバレッジの確保

カバレッジ80%を維持するための原則:

- **新規機能**: 実装と同時にテストも書く（後回しにしない）
- **エッジケース**: 正常系だけでなく異常系もテスト
- **リファクタリング**: テストが通ることを確認しながら進める

詳細な確認方法は[docs/testing.md](docs/testing.md)を参照してください。

### 実装前の確認事項

コードを書き始める前に確認:

- [ ] 既存の類似実装を確認（DRY原則）
- [ ] 変更の影響範囲を把握
- [ ] テスト戦略を考える（どのようなテストが必要か）
- [ ] カバレッジを維持できるか確認

実装完了後の確認:

- [ ] すべてのチェックコマンドが通過
- [ ] カバレッジが80%以上
- [ ] 新規/変更機能にテストが追加されている
- [ ] コミットメッセージがConventional Commits形式

---

## プロジェクト概要

LLM Skills機能を使用して、日本の伝統的な履歴書フォーマット（JIS規格準拠）を自動生成するツール。
入力されたデータから、印刷可能な高品質な履歴書をPDF形式で出力します。

**詳細仕様**: [docs/specifications.md](docs/specifications.md)を参照してください。

## 機能要件（概要）

### 主要機能

1. **JIS規格準拠の履歴書レイアウト生成**
   - A4/B5用紙サイズ対応（既定値: A4）
   - 和暦/西暦表記切り替え（既定値: 西暦）
   - 正式名称による記載（略語禁止）

2. **PDF形式での出力**
   - 印刷可能な高品質PDF生成
   - カスタムフォント埋め込み対応

3. **構造化データ入出力**
   - YAML/JSON形式でのデータ入力
   - JSON Schema準拠のバリデーション

### オプション設定

| オプション | 既定値 | 設定方法 |
|-----------|--------|---------|
| 和暦/西暦 | 西暦 | セッション: 「和暦で表記してください」<br>恒久: `config.yaml` で `date_format: wareki` |
| 用紙サイズ | A4 | セッション: 「B5サイズで作成してください」<br>恒久: `config.yaml` で `paper_size: B5` |

## アーキテクチャ方針

### 実装言語

**Python 3.11+**

- 型ヒント（Type Hints）による型安全性
- ReportLabによる高品質なPDF生成
- PyYAMLとjsonschemaによるデータ処理

### ディレクトリ構造（重要部分のみ）

```
jtr-generator/
├── src/                    # 共通実装（LLM非依存）
│   ├── models/             # データモデル定義
│   ├── generators/         # PDF生成ロジック
│   ├── validators/         # 入力データ検証
│   └── formatters/         # 日付・テキスト整形
├── data/layouts/           # レイアウト定義（PDF罫線座標データ）
├── schemas/                # JSON Schema定義
├── examples/               # サンプルデータ
├── platforms/              # プラットフォーム別実装
│   ├── claude/             # Claude Skills用
│   └── ...
├── tests/                  # テストコード
└── docs/                   # 詳細ドキュメント
```

### マルチプラットフォーム対応

**設計方針:**
- **src/**: LLM非依存の共通実装（再利用可能）
- **platforms/**: 各LLMプラットフォーム固有の統合コード

**詳細**: [docs/specifications.md - アーキテクチャ](docs/specifications.md)を参照してください。

## 共通実装インターフェース

### PDF生成

```python
from typing import Dict, Any
from pathlib import Path

def generate_resume_pdf(
    data: Dict[str, Any],
    options: Dict[str, Any],
    output_path: Path
) -> None:
    """
    履歴書PDFを生成（LLM非依存）

    Args:
        data: schemas/resume_schema.jsonに準拠した履歴書データ
        options: 生成オプション（LLM環境から注入される）
            - paper_size: 'A4' or 'B5'
            - date_format: 'seireki' or 'wareki'
            - fonts: フォント設定（LLM環境依存）
                - main: 本文フォントの絶対パス
                - heading: 見出しフォントの絶対パス（optional）
        output_path: 出力PDFファイルパス

    Raises:
        ValidationError: データがスキーマに準拠しない場合
        FontError: フォントファイルが見つからない場合
    """
    pass
```

### データ読み込み

```python
def load_resume_data(file_path: Path) -> Dict[str, Any]:
    """
    YAML/JSONファイルから履歴書データを読み込み（LLM非依存）

    Args:
        file_path: YAMLまたはJSONファイルのパス

    Returns:
        履歴書データ（JSON Schema準拠）

    Raises:
        ValidationError: スキーマバリデーション失敗時
        FileNotFoundError: ファイルが存在しない場合
    """
    pass
```

## 重要な禁止事項

### 略語の禁止

履歴書では以下の略語は**絶対に使用禁止**です:

- 「㈱」→「株式会社」
- 「高」→「高等学校」
- その他すべての略語

**正式名称を必ず使用してください。**

### セキュリティ

- ユーザー入力は常にサニタイズ
- ファイルパスはバリデーション（パストラバーサル対策）
- 機密情報（APIキー等）は含めない

## 関連ドキュメント

- **詳細仕様**: [docs/specifications.md](docs/specifications.md)
- **検証・テスト**: [docs/testing.md](docs/testing.md)
- **開発計画**: [docs/roadmap.md](docs/roadmap.md)
- **レイアウト調整**: [docs/layout_alignment.md](docs/layout_alignment.md)
- **Claude Skills固有**: [CLAUDE.md](CLAUDE.md)
