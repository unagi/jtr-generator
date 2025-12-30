# Agent Skills - 技術仕様

## ⚠️ 重要な変更（2025年12月）

**ディレクトリ構成が変更されました:**

- **変更前**: `platforms/claude/` ディレクトリに配置
- **変更後**: リポジトリでは `skill/` 配下に統一配置（`SKILL.md`, `main.py`, `config.yaml`, `README.md`）
- **ビルド成果物**: これらがルート直下に展開される
- **理由**: Codexでも同一のzipファイルが動作することが確認されたため、プラットフォーム分離を廃止

**このドキュメントは、Agent Skills固有の技術仕様（Beta API、Files API等）をまとめたものです。**

詳細な経緯は[AGENTS.md - Agent Skills仕様準拠](AGENTS.md#agent-skills仕様準拠)を参照してください。

## 概要

**対象読者**: Agent Skillsを使用してカスタムスキルを開発・デバッグする開発者

**プロジェクト全体の仕様**: [AGENTS.md](AGENTS.md)を参照してください。

**共通実装インターフェース**: [AGENTS.md - 共通実装インターフェース](AGENTS.md#共通実装インターフェース)を参照してください。

## 使用方法

### エンドユーザー（Claude.ai）

エンドユーザー向けの使い方は[README.md](README.md)を参照してください。
カスタムスキルをClaude.aiにアップロードして使用します。

### 開発者（ローカル開発・デバッグ）

このドキュメントでは、ローカル環境でのSkills開発・デバッグ方法を説明します。

## Agent Skills構成

### ルート配置ファイル（リポジトリ）

```
jtr-generator/
├── skill/                  # 配布パッケージのルート相当
│   ├── SKILL.md            # Agent Skills定義ファイル（YAMLフロントマター + 指示）
│   ├── main.py             # エントリーポイント
│   ├── config.yaml         # ユーザー設定テンプレート
│   ├── README.md           # エンドユーザー向け使用方法
│   ├── jtr/                # 共通実装
│   ├── data/               # レイアウトデータ
│   ├── schemas/            # JSON Schema
│   ├── examples/           # サンプルデータ
│   └── fonts/              # デフォルトフォント
```

**ビルド成果物** (`build/jtr-generator.zip`):
```
jtr-generator.zip/
├── SKILL.md
├── main.py
├── config.yaml
├── README.md
├── requirements.txt        # 自動生成
├── jtr/                    # 必要なモジュールのみ
├── data/                   # レイアウトデータ
├── schemas/
├── fonts/
└── examples/
```

### SKILL.md

Agent Skillsのメタデータ定義とLLM向け指示を統合したファイル:

```markdown
---
name: jtr-generator
description: JIS規格準拠の日本の履歴書をPDF形式で生成するSkill。対話的な情報収集またはYAML/JSONファイルからPDF生成が可能。
---

# 日本の履歴書生成Skill

## Overview
...

## Data Collection Rules
...
```

**重要な変更点**:
- ~~skill.json~~ → **SKILL.md**（YAMLフロントマター形式）
- ~~INSTRUCTION.md~~ → **SKILL.mdに統合**
- 公式仕様: https://agentskills.io

### Progressive Disclosure

Claude Skillsは3段階の情報提供パターンを推奨します。
main.pyのモジュールdocstringで実装:

```python
"""
日本の履歴書生成Skill

Overview:
JIS規格準拠の日本の履歴書をPDF形式で生成します。
対話的な情報収集またはYAML/JSONファイルからの生成が可能です。

Details:
- 入力形式: チャットテキスト、YAML、JSON
- 出力形式: PDF（A4のみ、和暦/西暦切り替え可能）
- カスタムフォント対応
- JSON Schema準拠のバリデーション

Examples:
1. 対話的生成:
   「履歴書を作成してください。氏名は山田太郎です。」

2. ファイルからの生成:
   [YAMLファイルを添付] 「このファイルから履歴書を生成してください。」

3. オプション指定:
   「A4サイズ、和暦で履歴書を作成してください。」
"""
```

## 共通実装との接点

### エントリーポイント（main.py）

Claude Skills環境から値を取得し、共通インターフェースに注入します:

```python
from pathlib import Path
from typing import Any

from jtr import (
    generate_resume_pdf,
    load_config,
    resolve_font_paths,
    validate_and_load_data,
)


def main(
    input_data: str | Path,
    session_options: dict[str, Any] | None = None,
    output_path: Path | str | None = None,
) -> Path:
    """
    Claude Skills環境から呼び出されるメイン関数

    Args:
        input_data: ユーザーが提供したYAML/JSONデータ（文字列またはファイルパス）
        session_options: セッション固有のオプション（和暦/西暦、用紙サイズ等）
        output_path: 出力PDFファイルのパス（Noneの場合はカレントにrirekisho.pdf）

    Returns:
        生成されたPDFファイルのパス
    """
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path if config_path.exists() else None)
    config = resolve_font_paths(config, Path(__file__).parent)

    if session_options:
        if "date_format" in session_options:
            config["options"]["date_format"] = session_options["date_format"]
        if "paper_size" in session_options:
            config["options"]["paper_size"] = session_options["paper_size"]

    data = validate_and_load_data(input_data)

    options = dict(config.get("options", {}))
    options["fonts"] = config.get("fonts", {})

    final_output_path = Path(output_path) if output_path else Path("rirekisho.pdf")
    generate_resume_pdf(data, options, final_output_path)
    return final_output_path
```

### 設定注入パターン

**Claude Skills固有の処理:**
1. `config.yaml` の読み込み
2. 相対パス → 絶対パスの解決
3. 作業ディレクトリの取得
4. 環境変数の取得（必要に応じて）

**共通インターフェースへの注入:**
- `options` 辞書にすべての設定を格納
- フォントパスは絶対パスに解決済み
- `generate_resume_pdf(data, options, output_path)` を呼び出し

## Claude Skills実行環境の制約

### VMベースの実行

Claude Skillsはサンドボックス化されたVM環境で実行されます:

**制約事項:**
- **ネットワークアクセス**: 制限あり（外部APIへのアクセス不可）
- **ファイルシステム**: 一時的な作業ディレクトリ（`/tmp`）のみ書き込み可
- **実行時間制限**: 数分程度
- **メモリ制限**: 詳細は公式ドキュメント参照

**利用可能な機能:**
- パッケージに含まれるPythonライブラリ
- ファイルの読み書き（一時ディレクトリ内）
- 標準ライブラリ

### セキュリティ上の注意

- ユーザー入力は常にサニタイズ
- ファイルパスはバリデーション（パストラバーサル対策）
- 機密情報（APIキー等）は含めない
- 外部リソースへのアクセス不可

## ローカル開発環境

### セットアップ

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージのインストール
pip install anthropic>=0.71.0 reportlab pyyaml jsonschema

# 環境変数の設定
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Beta API仕様

#### 必須要件

Claude Skills APIは現在Beta版です。以下の要件を満たす必要があります。

**1. Beta名前空間の使用**

```python
from anthropic import Anthropic

client = Anthropic()

# ✅ 正解
response = client.beta.messages.create(...)

# ❌ 誤り
response = client.messages.create(...)  # Skillsは使えない
```

**2. Betaヘッダーの指定**

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=[
        "code-execution-2025-08-25",
        "files-api-2025-04-14",
        "skills-2025-10-02"
    ],
    container={
        "type": "code_execution_20250825",
        "skills": ["pdf"]
    },
    messages=[...]
)
```

**3. Code Execution必須**

Skills APIは内部でCode Executionを使用するため、`code_execution_20250825`が必須です。

### Files API統合

#### ファイルIDの抽出

```python
def extract_file_ids(response):
    """レスポンスからfile_idを抽出"""
    file_ids = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "bash_code_execution_20250825":
            for content_item in block.content:
                if hasattr(content_item, 'file_id'):
                    file_ids.append(content_item.file_id)
    return file_ids
```

#### ファイルのダウンロード

```python
# ✅ 正解
file_content = client.beta.files.download(file_id)
with open(output_path, 'wb') as f:
    f.write(file_content.read())  # .read()を使用

# ❌ 誤り
f.write(file_content.content)  # .content属性は存在しない
```

#### メタデータの取得

```python
metadata = client.beta.files.retrieve_metadata(file_id)

# 利用可能なフィールド
print(f"ファイル名: {metadata.filename}")
print(f"サイズ: {metadata.size_bytes} bytes")  # size_bytes（sizeではない）
print(f"MIME: {metadata.mime_type}")
```

## トラブルシューティング

### よくある問題

#### 1. SDKバージョン

**問題**: `client.beta.messages.create()`が存在しない

**解決**: Anthropic SDK 0.71.0以降をインストール

```bash
pip install anthropic>=0.71.0
python -c "import anthropic; print(anthropic.__version__)"
```

#### 2. Beta名前空間

**問題**: `container`パラメータが認識されない

**解決**: `client.beta.messages.create()`を使用（`client.messages.create()`ではない）

#### 3. Betaヘッダー配置

**問題**: 全リクエストでcode_executionが要求される

**解決**: `default_headers`ではなく、リクエストごとに`betas`パラメータを使用

```python
# ❌ 誤り
client = Anthropic(default_headers={"anthropic-beta": "skills-2025-10-02"})

# ✅ 正解
response = client.beta.messages.create(
    betas=["code-execution-2025-08-25", "files-api-2025-04-14", "skills-2025-10-02"],
    ...
)
```

#### 4. ファイルダウンロード

**問題**: `'BinaryAPIResponse' object has no attribute 'content'`

**解決**: `.content`ではなく`.read()`を使用

#### 5. メタデータサイズ

**問題**: `'FileMetadata' object has no attribute 'size'`

**解決**: `.size`ではなく`.size_bytes`を使用

#### 6. 生成時間

**実測時間**: PDF生成は1-2分程度かかります

**対策**: タイムアウトを適切に設定

```python
client = Anthropic(
    api_key="your-api-key",
    timeout=180.0  # 3分
)
```

### デバッグチェックリスト

1. ✅ SDKバージョン: `anthropic.__version__ >= 0.71.0`
2. ✅ Beta名前空間: `client.beta.messages.create()`を使用
3. ✅ Betaヘッダー: `betas`パラメータで指定
4. ✅ Container: `container`パラメータが正しく設定
5. ✅ レスポンス確認: `print(response)`でデバッグ
6. ✅ エラー詳細: `response.stop_reason`を確認

## 実装例

### 基本的なPDF生成（ローカル開発）

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 履歴書データ（JSON Schemaに準拠）
resume_data = {
    "personal_info": {
        "name": "山田太郎",
        "name_kana": "やまだたろう",
        "birthdate": "1990-04-01",
        "gender": "男性",
        "postal_code": "150-0041",
        "address": "東京都渋谷区神南1-1-1",
        "phone": "03-1234-5678",
        "mobile": "090-1234-5678",
        "email": "yamada@example.com"
    },
    "education": [...],
    "work_history": [...],
    "qualifications": [...],
    "additional_info": {...}
}

# PDF履歴書の生成
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "files-api-2025-04-14", "skills-2025-10-02"],
    container={
        "type": "code_execution_20250825",
        "skills": ["pdf"]
    },
    messages=[
        {
            "role": "user",
            "content": f"""
日本の履歴書をPDF形式で作成してください。

データ:
{resume_data}

要件:
- JIS規格準拠のレイアウト
- A4サイズ
- 西暦表記
- 証明写真エリアを含む
- すべての項目に適切な罫線
"""
        }
    ]
)

# ファイルIDを抽出してダウンロード
file_ids = extract_file_ids(response)
for file_id in file_ids:
    file_content = client.beta.files.download(file_id)
    with open(f"outputs/rirekisho.pdf", "wb") as f:
        f.write(file_content.read())
    print(f"履歴書を生成しました: rirekisho.pdf")
```

## リソース

### 公式ドキュメント

- **Messages API**: https://docs.claude.com/en/api/messages
- **Files API**: https://docs.claude.com/en/api/files-content
- **Skills Documentation**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview

### SDK

- **Anthropic Python SDK**: https://github.com/anthropics/anthropic-sdk-python
- **リリースノート**: CHANGELOGでBeta API対応を確認

### 関連ドキュメント

- [README.md](README.md) - エンドユーザー向け使い方ガイド
- [AGENTS.md](AGENTS.md) - プロジェクト全体仕様（LLM非依存）
- [skill/assets/schemas/resume_schema.json](skill/assets/schemas/resume_schema.json) - データスキーマ定義

## 今後のAPI変更

Skills APIは現在Beta版です。正式リリース時に以下の変更が予想されます:

- Betaヘッダーの不要化
- 名前空間の変更（`client.beta.*` → `client.*`）
- レスポンス構造の変更

定期的に公式ドキュメントを確認し、最新仕様に追従してください。
