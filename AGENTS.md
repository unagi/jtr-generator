# jtr-generator - 日本の履歴書生成ツール

## プロジェクト概要

LLM Skills機能を使用して、日本の伝統的な履歴書フォーマット（JIS規格準拠）を自動生成するツール。
入力されたデータから、印刷可能な高品質な履歴書をPDF形式で出力します。
データはYAML/JSON形式で入出力でき、バックアップ・編集・再利用が可能です。

## 機能要件

### 主要機能

1. **JIS規格準拠の履歴書レイアウト生成**
   - A4/B5用紙サイズ対応（既定値: A4）
   - 和暦/西暦表記切り替え（既定値: 西暦）
   - 正式名称による記載（略語禁止）

2. **PDF形式での出力**
   - 印刷可能な高品質PDF生成
   - カスタムフォント埋め込み対応
   - 300dpi以上の解像度

3. **構造化データ入出力**
   - YAML/JSON形式でのデータ入力
   - JSON Schema準拠のバリデーション
   - データのバックアップ・リストア機能

4. **カスタムフォント設定**
   - ユーザー提供フォントの使用
   - `config.yaml`での設定
   - ライセンス上の理由により非同梱

### 生成方法

1. **対話的生成**
   - チャット内テキストから情報抽出
   - 不足項目の対話的な質問
   - 段階的な情報収集

2. **構造化データからの生成**
   - YAMLファイルからの直接生成
   - JSONファイルからの直接生成
   - スキーマバリデーション

### オプション設定

| オプション | 既定値 | 設定方法 |
|-----------|--------|---------|
| 和暦/西暦 | 西暦 | セッション: 「和暦で表記してください」<br>恒久: `config.yaml` で `date_format: wareki` |
| 用紙サイズ | A4 | セッション: 「B5サイズで作成してください」<br>恒久: `config.yaml` で `paper_size: B5` |

## ドメイン知識：日本の履歴書仕様

### 用紙・レイアウト規格

- **用紙サイズ**: A4（297mm × 210mm）またはB5（257mm × 182mm）
- **印刷**: 片面印刷、縦方向
- **余白**: 上下左右それぞれ10-15mm程度
- **フォント**: 明朝体が基本、見出しはゴシック体も可

### 必須記載項目

#### 1. 基本情報
- 氏名（ふりがな付き）
- 生年月日（和暦/西暦）
- 年齢
- 性別
- 証明写真（縦40mm × 横30mm、3ヶ月以内撮影）

#### 2. 連絡先情報
- 現住所（都道府県から番地まで）
- 郵便番号
- 電話番号（固定電話/携帯電話）
- メールアドレス

#### 3. 学歴
- 時系列順（古い順）
- 小学校卒業から記載が一般的
- 「〇〇高等学校 卒業」のように正式名称
- 和暦または西暦（統一）

#### 4. 職歴
- 時系列順（古い順）
- 会社名は正式名称（株式会社の位置に注意）
- 入社・退職の理由（「一身上の都合により退職」等）
- 現職の場合は「現在に至る」

#### 5. 資格・免許
- 取得年月順
- 正式名称（「普通自動車第一種運転免許」等）

#### 6. 志望動機・自己PR
- 200-300文字程度
- 企業ごとにカスタマイズ可能

### 書式ルール

#### 年号表記
- 和暦（令和、平成、昭和）または西暦
- ドキュメント内で統一すること
- 西暦の場合は4桁表記

#### 敬称・表記
- 学校名：「〇〇高等学校」（「高校」と略さない）
- 会社名：「株式会社〇〇」「〇〇株式会社」（正式名称）
- 学部・学科：正式名称（「工学部 情報工学科」等）
- 卒業/修了：「卒業」「修了」を正確に使い分け

#### 禁止事項
- 略語の使用（「㈱」「高」等）
- 誤字・脱字
- 修正液の使用（印刷後の修正不可）

## データモデル設計

### 概要

履歴書データは以下の5つのセクションで構成されます:

```yaml
personal_info:      # 個人情報（氏名、生年月日、連絡先等）
education:          # 学歴（配列）
work_history:       # 職歴（配列）
qualifications:     # 資格・免許（配列）
additional_info:    # 志望動機・自己PR
```

### 詳細仕様

データモデルの詳細は **JSON Schema** で定義されています:
- **スキーマファイル**: `schemas/resume_schema.json`
- **サンプルデータ**: `examples/sample_resume.yaml` および `examples/sample_resume.json`

### データ形式要件

- **入力形式**: YAML または JSON
- **バリデーション**: YAMLは処理前にJSON化され、JSON Schemaと突合
- **マルチライン**: YAMLは `|` 記法で改行を保持、JSONは `\n` エスケープ
- **日付形式**: ISO 8601形式（`YYYY-MM-DD` または `YYYY-MM`）
- **必須フィールド**: スキーマの `required` プロパティで定義
- **列挙型**: 性別、学歴・職歴の種別等はスキーマで定義された値のみ許可

## アーキテクチャ方針

### 実装言語

**Python 3.11+**

すべての実装はPythonで統一します。これにより:
- 型ヒント（Type Hints）による型安全性
- ReportLabによる高品質なPDF生成
- PyYAMLとjsonschemaによるデータ処理
- 豊富なエコシステムとライブラリ

### ディレクトリ構造

```
jtr-generator/
├── src/                    # 共通実装（LLM非依存）
│   ├── models/             # データモデル定義
│   ├── generators/         # PDF生成ロジック
│   ├── validators/         # 入力データ検証
│   └── formatters/         # 日付・テキスト整形
├── schemas/                # JSON Schema定義
│   └── resume_schema.json
├── examples/               # サンプルデータ
│   ├── sample_resume.yaml
│   └── sample_resume.json
├── platforms/              # プラットフォーム別実装
│   ├── claude/             # Claude Skills用
│   │   ├── skill.json      # Claude Skills定義
│   │   ├── main.py         # エントリーポイント
│   │   ├── config.yaml     # ユーザー設定テンプレート
│   │   └── README.md       # Claude固有の説明
│   ├── gemini/             # Gemini Skills用（将来）
│   │   └── ...
│   └── chatgpt/            # ChatGPT Skills用（将来）
│       └── ...
├── build/                  # ビルド出力
│   ├── claude.zip          # Claude Skillsパッケージ
│   ├── gemini.zip          # Gemini Skillsパッケージ（将来）
│   └── chatgpt.zip         # ChatGPT Skillsパッケージ（将来）
├── fonts/                  # フォント配置先（ユーザーが配置）
│   ├── .gitkeep
│   └── README.md           # フォント配置方法の説明
├── tests/                  # テストコード
└── docs/                   # ドキュメント
```

### マルチプラットフォーム対応

**設計方針:**
- **src/**: LLM非依存の共通実装（再利用可能）
- **platforms/**: 各LLMプラットフォーム固有の統合コード
- **build/**: 各プラットフォーム向けのパッケージ（ZIP）

**ビルドプロセス:**

各プラットフォームのパッケージ（例: `build/claude.zip`）は以下を含む:
1. `src/` の共通実装
2. `schemas/` のスキーマ定義
3. `platforms/{platform}/` の固有ファイル
4. ユーザーが配置した `fonts/`（オプション）

**プラットフォーム別の責務:**

| コンポーネント | 説明 | 共通 | Claude | Gemini | ChatGPT |
|---------------|------|------|--------|--------|---------|
| src/* | 実装ロジック | ✅ | - | - | - |
| schemas/* | データ定義 | ✅ | - | - | - |
| skill.json | メタデータ | - | ✅ | ✅ | ✅ |
| main.py | エントリーポイント | - | ✅ | ✅ | ✅ |
| config.yaml | 設定テンプレート | - | ✅ | ✅ | ✅ |

### モジュール分割方針

**src/models/** - データモデル定義
- Python dataclassesまたはPydanticを使用
- 型安全性を重視
- JSON Schemaとの整合性を保つ

**src/generators/** - PDF生成ロジック
- ReportLabを使用した高品質PDF生成
- JIS規格準拠のレイアウト実装
- フォント設定は外部から注入

**src/validators/** - バリデーション
- JSON Schema突合
- 必須項目チェック
- フォーマット検証

**src/formatters/** - ユーティリティ
- 和暦変換（西暦 ↔ 令和/平成/昭和）
- 正式名称変換
- 日付フォーマット

### 共通実装インターフェース

#### PDF生成

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

#### データ読み込み

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

#### 対話的生成

```python
def extract_info_from_text(text: str) -> tuple[Dict[str, Any], list[str]]:
    """
    チャットテキストから履歴書情報を抽出（LLM依存部分あり）

    Args:
        text: ユーザー入力テキスト

    Returns:
        (抽出された情報, 不足している必須項目のリスト)
    """
    pass

def generate_questions(missing_fields: list[str]) -> str:
    """
    不足項目に対する質問を生成（LLM非依存）

    Args:
        missing_fields: 不足している項目のリスト

    Returns:
        質問テキスト
    """
    pass
```

### 設定ファイル（config.yaml）

プラットフォーム固有ディレクトリ（例: `platforms/claude/config.yaml`）に配置:

```yaml
options:
  date_format: seireki    # 'seireki' or 'wareki'
  paper_size: A4          # 'A4' or 'B5'

fonts:
  main: fonts/main.ttf           # 本文用フォント（相対パス）
  heading: fonts/heading.ttf     # 見出し用フォント（相対パス、optional）
```

**注意**: フォントパスは相対パスで記述し、各プラットフォームの実装（main.py）で絶対パスに解決します。

## 出力フォーマット要件

### PDF形式（.pdf）

- **ページサイズ**: A4/B5
- **フォント埋め込み**: 必須（印刷互換性のため）
- **解像度**: 300dpi以上推奨
- **証明写真エリア**: 縦40mm × 横30mm（画像は手動配置）
- **罫線**: すべての項目に適切な罫線
- **余白**: 上下左右10-15mm

## 検証・テスト方針

### フォーマット検証

- [ ] すべての必須項目が記載されているか
- [ ] 年号表記が統一されているか（和暦/西暦混在なし）
- [ ] 正式名称が使用されているか（略語なし）
- [ ] 時系列が正しいか（古い順）

### レイアウト検証

- [ ] 証明写真エリアのサイズが正しいか
- [ ] 各項目の配置が適切か
- [ ] 罫線が欠けていないか
- [ ] フォントサイズが読みやすいか
- [ ] 長いテキストが適切に改行・配置されるか

### 印刷検証

- [ ] A4/B5用紙に正しく印刷されるか
- [ ] 余白が適切か
- [ ] 文字が切れていないか
- [ ] 実機での印刷テスト

### データ整合性検証

- [ ] 生年月日から年齢が正しく計算されているか
- [ ] 学歴・職歴の時系列に矛盾がないか
- [ ] 資格取得年月が生年月日より後か
- [ ] JSON Schemaに準拠しているか

## 開発ロードマップ

### Phase 1: 基盤構築
- [ ] JSON Schema定義
- [ ] データモデル定義（型定義）
- [ ] バリデーション機能実装
- [ ] 和暦変換ユーティリティ

### Phase 2: PDF生成実装
- [ ] Skills API統合
- [ ] PDF生成実装
- [ ] フォント埋め込み対応
- [ ] サンプルデータでの動作確認

### Phase 3: レイアウト最適化
- [ ] JIS規格準拠のレイアウト調整
- [ ] 証明写真エリア配置
- [ ] フォント・罫線の調整
- [ ] 長文テキストの改行処理

### Phase 4: データ入出力
- [ ] YAML/JSON読み込み実装
- [ ] スキーマバリデーション統合
- [ ] データエクスポート機能
- [ ] エラーメッセージの多言語化

### Phase 5: 対話的生成
- [ ] チャットテキストからの情報抽出
- [ ] 不足項目の検出
- [ ] 対話的な質問生成
- [ ] 段階的データ収集

### Phase 6: カスタマイズ機能
- [ ] config.yaml読み込み
- [ ] カスタムフォント設定
- [ ] オプション設定（和暦/西暦、用紙サイズ）
- [ ] セッション設定とデフォルト設定の分離

### Phase 7: 拡張機能
- [ ] 職務経歴書対応
- [ ] 複数テンプレート（業種別等）
- [ ] 英文レジュメ対応

## 制限事項

### 現在の制限

- **証明写真**: 画像パスの指定のみ対応、自動埋め込みは未対応
- **職歴件数**: 転職回数が10回を超える場合、レイアウトが崩れる可能性
- **カスタムレイアウト**: 標準的なJIS規格フォーマットのみ対応

### 技術的制約

- **フォント**: ライセンス上の理由により非同梱、ユーザー提供必須
- **生成時間**: LLM Skills APIの仕様により1-2分程度かかる
- **ファイルサイズ**: 生成PDFは通常1MB以下

## 将来の拡張性

### 想定される追加機能

- 職務経歴書生成
- 英文レジュメ対応
- 複数テンプレート（業種別、デザイン別）
- 証明写真の自動埋め込み
- オンラインプレビュー機能

### 他のLLM対応

プロジェクトアーキテクチャはLLM非依存で設計。
将来的にGemini、OpenAI等の同様のドキュメント生成機能への対応が可能。

各LLMプラットフォーム固有の実装詳細は、以下のドキュメントに分離:
- `CLAUDE.md` - Claude Skills API仕様
- `GEMINI.md` - Gemini Skills相当機能（将来）
- `OPENAI.md` - OpenAI Skills相当機能（将来）

## 参考情報

### JIS規格
- JIS Z 8303（帳票の設計基準）
- 一般的な履歴書フォーマットはJIS規格に準拠

### データソース
- ハローワーク推奨履歴書フォーマット
- 厚生労働省履歴書様式例

### 日本語フォント
- IPAフォント: https://moji.or.jp/ipafont/
- Noto Sans JP: https://fonts.google.com/noto/specimen/Noto+Sans+JP
- 源ノ角ゴシック: https://github.com/adobe-fonts/source-han-sans
- BIZ UDゴシック/明朝: https://github.com/googlefonts/morisawa-biz-ud-gothic
