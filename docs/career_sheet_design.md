# 職務経歴書機能の設計仕様

**作成日**: 2025-12-30
**ステータス**: 設計フェーズ（実装前）

---

## 概要

日本の転職市場で使用される職務経歴書（Shokumu Keirekisho）をPDF形式で生成する機能を追加します。
履歴書が規格化されたフォーマットであるのに対し、職務経歴書は自由度が高く、LLMの支援が特に効果的な領域です。

---

## 前提条件

### Agent Skills標準構造への準拠

実装時は以下のAgent Skills標準ディレクトリ構造に準拠します：

```
skill/
├── SKILL.md              # Agent Skills定義ファイル（必須）
├── scripts/              # 実行可能コード（Python実装）
│   ├── main.py           # エントリーポイント
│   └── jtr/              # 共通実装モジュール
├── references/           # ドキュメント（ベストプラクティス等）
└── assets/               # リソース（スキーマ、テンプレート、フォント等）
    ├── config.yaml
    ├── schemas/
    ├── data/
    ├── fonts/
    └── examples/
```

**✅ 完了**: ディレクトリ構造はAgent Skills標準に準拠済みです（2025-12-30）。

**重要な変更点**:
- 履歴書生成の既存コードはすべて `scripts/jtr/` に移動済み
- パス参照はすべて `assets/` 経由に修正済み
- テストは129件パス、カバレッジ91%達成

---

## 機能要件

### 基本方針

1. **入力形式**: Markdown（自由記述のリッチテキスト）
2. **テンプレート項目**:
   - 個人情報（氏名、生年月日、電話、メール）
   - 免許・資格
   - これらは履歴書データから自動生成し、Markdownには含めない
3. **レイアウト分離**:
   - 構造データ領域（プロフィール/免許・資格）とMarkdown領域を明確に分離
   - Markdownのトップレベル見出しは **H2（##）** として扱う（`#`はH2に正規化）
4. **PDF生成**: LLMがMarkdownからリッチテキストに変換してPDF化
5. **デザイン**: Web調査とベストプラクティスに基づく標準的なレイアウト

### デザインルール（現行）

- **配色**: モノクロ + 追加3色（本文/メイン/サブ/アクセント）
  - 設定は `skill/assets/config.yaml` の `styles.colors` で管理
  - サブカラーは背景・罫線などの加飾専用（文字色には使用しない）
- **整列**: 左寄せを基本、日付のみ右寄せ
- **余白**: 2mm基準のトークンで統一
- **箇条書き**: ぶら下げインデントで視認性を確保

### DOCX参照解析（デザイン抽出）

- 参照DOCX（`tests/fixtures/resume_sample.docx`）を解析し、ReportLab用の加飾定義の素案を抽出
- 解析スクリプト: `tools/analyze_docx_styles.py`
- 出力: `skill/assets/data/career_sheet/docx_style_report.json`

### HTML媒介アプローチの比較（職務経歴書）

#### 方針
- **OS非依存のPDF生成ライブラリ**を前提に選定する（Agent Skillsの制約）。

#### 候補A: ReportLab Flowables（現行）
- **長所**: レイアウト制御が細かい。既存コード資産と整合。
- **短所**: HTML/CSS的な表現が難しく、Markdown要素の装飾ロジックが増えやすい。

#### 候補B: fpdf2 の HTML媒介
- **概要**: `FPDF.write_html()` でHTMLをPDFに変換する方式。
- **対応範囲（v2系ドキュメント前提）**:
  - HTMLの基本要素（見出し/段落/リスト/表/リンク/太字など）に対応。
  - HTMLパーサはPython標準の `html.parser.HTMLParser` を使用。
  - CSSは**非サポート**（限定的な属性のみ、Tailwindのclass適用は不可）。
- Markdownは Mistune でHTMLに変換可能。
- **長所**: Markdown → HTML → PDFの流れが整理しやすい。
- **短所**: CSSが使えないため、装飾はHTML要素と限定属性に集約する必要がある。

#### 候補C: OSネイティブ依存のHTML→PDFエンジン
- **扱い**: Agent Skillsの制約により**不採用**。

#### 判断基準
- OS非依存で動作すること
- Markdown要素に対する**論理的な装飾**が可能か
- 余白/加飾（罫線・背景）の制御性
- 既存の履歴書（ReportLab）との共存性

### 対応するMarkdown構文（GFM）

Mistune v3 + GFM相当プラグインで解析し、ReportLabへ変換する。

- **見出し**: `##` (H2) をトップレベルとして扱う（`#`はH2に正規化）
- **箇条書き**: `- item` / タスク（`- [x]`）
- **太字/斜体**: `**bold**` / `*italic*`
- **取り消し線**: `~~strike~~`
- **リンク**: `https://example.com` / `[text](url)`
- **水平線**: `---`
- **コード**: インライン `` `code` `` / ブロック ````` ``` `````
- **テーブル**: GFMテーブル構文

---

## アーキテクチャ設計

### ディレクトリ構造（Agent Skills標準準拠）

```
skill/
├── SKILL.md                                        # 更新: 職務経歴書の説明追加
│
├── scripts/                                        # 実行可能コード
│   ├── main.py                                     # 更新: document_type分岐追加
│   └── jtr/                                        # 共通実装
│       ├── __init__.py                             # 更新: 新規関数のエクスポート追加
│       ├── pdf_generator.py                       # 既存: 履歴書PDF生成
│       ├── career_sheet_generator.py              # 新規: 職務経歴書PDF生成
│       ├── markdown_to_richtext.py                # 新規: Markdown → リッチテキスト変換
│       ├── resume_data.py                         # 既存: データ読み込み・検証
│       ├── config.py                              # 既存: 設定管理
│       ├── japanese_era.py                        # 既存: 和暦変換
│       └── layout/                                # 既存: レイアウト計算
│
├── references/                                     # ドキュメント
│   ├── README.md                                   # 既存: エンドユーザー向け使用方法
│   └── career_sheet_best_practices.md             # 新規: 職務経歴書ベストプラクティス
│
└── assets/                                         # リソース・テンプレート
    ├── config.yaml                                 # 既存: 設定テンプレート
    ├── schemas/                                    # JSON Schema
    │   ├── resume_schema.json                     # 既存: 履歴書スキーマ
    │   └── career_sheet_schema.json               # 新規: 職務経歴書スキーマ
    ├── data/                                       # 既存: レイアウトデータ（履歴書用）
    ├── fonts/                                      # 既存: デフォルトフォント
    └── examples/                                   # サンプルデータ
        ├── sample_resume.yaml                     # 既存: 履歴書サンプル
        └── sample_career_sheet.yaml               # 新規: 職務経歴書サンプル
```

---

## データスキーマ設計

### JSON Schema (`assets/schemas/career_sheet_schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/unagi/jtr-generator/schemas/career_sheet_schema.json",
  "title": "Japanese Career Sheet",
  "description": "日本の職務経歴書データのスキーマ定義",
  "type": "object",
  "required": ["content"],
  "properties": {
    "resume_reference": {
      "type": "object",
      "description": "履歴書データからの参照（オプション、自動抽出用）",
      "properties": {
        "personal_info": {
          "type": "object",
          "description": "個人情報（履歴書のpersonal_infoから自動抽出）",
          "properties": {
            "name": {"type": "string"},
            "birthdate": {"type": "string", "format": "date"},
            "phone": {"type": "string"},
            "email": {"type": "string", "format": "email"}
          }
        },
        "qualifications": {
          "type": "array",
          "description": "免許・資格（履歴書のqualificationsから自動抽出）",
          "items": {
            "type": "object",
            "required": ["date", "name"],
            "properties": {
              "date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$"},
              "name": {"type": "string"}
            }
          }
        }
      }
    },
    "content": {
      "type": "string",
      "description": "職務経歴書本文（Markdown形式）。ベストプラクティス（PREP法、STAR法等）に従って構造化することを推奨。",
      "minLength": 1,
      "examples": [
        "# 職務要約\n\nデータ分析領域で8年の経験...\n\n## 職務経歴\n\n### 株式会社○○（2020-04 〜 2023-03）\n\n**Situation:** ...\n**Task:** ...\n**Action:** ...\n**Result:** ..."
      ]
    },
    "metadata": {
      "type": "object",
      "description": "メタデータ（生成オプション等）",
      "properties": {
        "format_type": {
          "type": "string",
          "enum": ["chronological", "reverse_chronological", "career"],
          "default": "reverse_chronological",
          "description": "フォーマット種別（逆時系列を推奨）"
        },
        "target_company": {
          "type": "string",
          "description": "応募企業名（カスタマイズ用、オプション）"
        },
        "job_description": {
          "type": "string",
          "description": "応募職種のJD（カスタマイズ用、オプション）"
        }
      }
    }
  },
  "additionalProperties": false
}
```

### サンプルデータ (`assets/examples/sample_career_sheet.yaml`)

```yaml
# 職務経歴書サンプルデータ

# 履歴書データからの参照（オプション）
resume_reference:
  personal_info:
    name: "山田太郎"
    birthdate: "1990-04-01"
    phone: "090-1234-5678"
    email: "yamada@example.com"
  qualifications:
    - date: "2015-06"
      name: "基本情報技術者試験 合格"
    - date: "2018-03"
      name: "AWS Certified Solutions Architect - Associate"

# 職務経歴書本文（Markdown形式）
content: |
  # 職務要約

  データ分析領域で8年の経験を持ち、前職では機械学習モデル導入により売上予測精度を40%向上。
  業界知識とPython/AWSスキルを活かし、貴社のデータドリブン経営に貢献いたします。

  ## 職務経歴

  ### 株式会社○○（2020-04 〜 2023-03）
  カスタマーサクセス部門 マネージャー

  **業種**: SaaS（従業員50名）

  #### 担当業務と実績

  **Situation（状況）:**
  創業5年のSaaS企業で、カスタマーサクセス部門の立ち上げを担当。
  顧客解約率が月5%と高く、収益成長の阻害要因となっていた。

  **Task（課題）:**
  解約率を3ヶ月で3%以下に低減し、年間MRR 1億円の維持を達成する。

  **Action（行動）:**
  - 顧客インタビュー20社実施し、解約理由を分析（オンボーディング不足が60%）
  - オンボーディングプログラムを再設計（初月導入支援を強化）
  - チャーンリスク予測モデルを構築（Python + Salesforceデータ連携）

  **Result（成果）:**
  - 解約率を5% → 2.5%に低減（目標達成）
  - MRR 1.2億円に成長（20%増）
  - Net Promoter Score（NPS）を30 → 55に改善

  ### 株式会社△△（2015-04 〜 2020-03）
  データアナリスト

  **業種**: EC（従業員300名）

  #### 担当業務と実績

  - 売上予測モデルの構築（Python/scikit-learn）
  - ダッシュボード開発（Tableau）による経営KPI可視化
  - A/Bテスト設計・分析（コンバージョン率15%向上）

  ## 活かせる経験・スキル

  ### 技術スキル
  - **Python（5年）**: 機械学習モデル構築（scikit-learn, TensorFlow）
  - **AWS（3年）**: EC2, S3, Lambda活用（AWS Solutions Architect Associate保有）
  - **SQL（7年）**: データ分析・可視化（PostgreSQL, BigQuery）

  ### ソフトスキル
  - **チームマネジメント**: 5名チームのリーダーとして年間目標120%達成
  - **問題解決力**: STAR法で構造化した課題解決（上記実績参照）

  ## 自己PR

  私のキャリアの軸は「データを活用した意思決定支援」です。
  前職では解約率低減プロジェクトを通じて、データ分析→施策立案→実行→検証のサイクルを確立しました。
  この経験を活かし、貴社のデータドリブン経営に貢献し、売上成長を加速させます。

# メタデータ（オプション）
metadata:
  format_type: "reverse_chronological"
  target_company: "株式会社サンプル"
  job_description: "データアナリスト（機械学習・AWS経験者歓迎）"
```

---

## ベストプラクティスリソース設計

### `references/career_sheet_best_practices.md`

人事からのアドバイスに基づく、LLM参照用のベストプラクティスガイドを作成します。

**主要な内容:**

1. **全体の原則**
   - 戦略的カスタマイズ（応募企業のJDに合わせて80%以上をカスタマイズ）
   - PREP法による構造化（Point-Reason-Example-Point）
   - 逆時系列（最新から）の徹底

2. **推奨される項目と並び順**
   - タイトル・個人情報
   - 職務要約（3-5行、PREP法適用）
   - 職務経歴（STAR法適用）
   - 活かせる経験・スキル
   - 自己PR

3. **STAR法の徹底**
   - Situation（状況）: 背景・課題の文脈
   - Task（課題）: 具体的に解決すべき課題
   - Action（行動）: 自分が取った行動
   - Result（成果）: **数字必須**（売上↑30%、コスト↓20%等）

4. **優秀者向けベストプラクティスTips**
   - 数字とエピソードで「再現性」を証明
   - 逆算で詳細度を調整（「ここだけは詳細に」）
   - 完璧主義を避け、合格点を目指す

5. **よくある失敗パターンと対策**
   - 業務内容の羅列 → STAR法で成果を明示
   - 時系列が古い順 → 逆時系列へ変更
   - 数値が抽象的 → 具体的な数値に変換

詳細は実装時に `references/career_sheet_best_practices.md` として作成します。

---

## モジュール設計

### 1. Markdown → リッチテキスト変換 (`scripts/jtr/markdown_to_richtext.py`)

```python
from typing import Any
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

def markdown_to_flowables(
    markdown: str,
    styles: dict[str, ParagraphStyle],
    decorations: dict[str, dict[str, Any]] | None = None,
) -> list[Any]:
    """
    Markdownテキストをreportlab Flowablesに変換

    対応するMarkdown構文（GFMサブセット）:
    - 見出し: ## (H2), ### (H3), #### (H4) ※ # はH2扱い
    - 箇条書き/タスク: - item / - [x] item
    - 太字/斜体/取り消し線: **bold** / *italic* / ~~strike~~
    - 段落: 空行で区切り
    - 水平線: ---
    - コード: `code` / ```code```
    - テーブル: GFMテーブル

    Args:
        markdown: Markdown形式のテキスト
        styles: ParagraphStyleの辞書
        decorations: 罫線やテーブルの加飾指定

    Returns:
        reportlab Flowablesのリスト

    Raises:
        KeyError: 必要なスタイルが存在しない場合
    """
    pass  # 実装は次PRで
```

**テストケース:**
- 見出し（H2/H3/H4）の変換
- 箇条書きの変換
- 太字の変換
- 段落の区切り
- 水平線・テーブル・タスクの変換
- 異常系（必須スタイル不足）

### 2. 職務経歴書PDF生成 (`scripts/jtr/career_sheet_generator.py`)

```python
from pathlib import Path
from typing import Any

def generate_career_sheet_pdf(
    data: dict[str, Any],
    options: dict[str, Any],
    output_path: Path,
) -> None:
    """
    職務経歴書PDFを生成

    Args:
        data: 職務経歴書データ（career_sheet_schema.jsonに準拠）
        options: 生成オプション（fonts等）
        output_path: 出力先PDFファイルパス

    Raises:
        ValidationError: データがスキーマに準拠しない場合
        FontError: フォントファイルが見つからない場合
    """
    pass  # 実装は次PRで


def _create_styles(font_name: str) -> dict[str, ParagraphStyle]:
    """スタイルシートを作成"""
    pass


def _create_header(
    metadata: dict[str, Any],
    styles: dict
) -> list:
    """ヘッダー（個人情報・資格）を作成"""
    pass
```

**テストケース:**
- 基本的なPDF生成
- 履歴書データとの統合（個人情報・資格の自動抽出）
- カスタムフォントの使用
- 異常系（不正なデータ、フォント不足等）

### 3. エントリーポイント統合 (`scripts/main.py`)

```python
def main(
    input_data: str | Path,
    document_type: str = "resume",  # "resume" or "career_sheet"
    session_options: dict[str, Any] | None = None,
    output_path: Path | str | None = None,
) -> Path:
    """
    Agent Skills環境から呼び出されるメイン関数

    Args:
        input_data: ユーザーが提供したYAML/JSONデータ
        document_type: "resume"（履歴書）または "career_sheet"（職務経歴書）
        session_options: セッション固有のオプション
        output_path: 出力PDFファイルのパス

    Returns:
        生成されたPDFファイルのパス

    Raises:
        ValueError: 不正なdocument_type
    """
    pass  # 実装は次PRで
```

---

## SKILL.md更新内容

### 追加セクション

```markdown
## Details

### Agent Skills標準構造

このSkillは以下の構造に従います：

```
skill/
├── SKILL.md              # このファイル
├── scripts/              # 実行可能コード（main.py, jtr/）
├── references/           # ドキュメント（README.md, career_sheet_best_practices.md）
└── assets/               # リソース（config.yaml, schemas/, data/, fonts/, examples/）
```

### 職務経歴書生成

#### ベストプラクティスの参照

職務経歴書作成時は、**必ず `references/career_sheet_best_practices.md` を参照**してください。

#### 対話的支援の流れ

**Step 1: ユーザーのレベルと目的を確認**
（初心者/経験者、応募企業情報の有無）

**Step 2: ベストプラクティスの提示**
（PREP法、STAR法の説明）

**Step 3: STAR法での構造化支援**
（Situation/Task/Action/Resultの聞き出し）

**Step 4: 数値化の徹底**
（曖昧な表現を数値に変換）

**Step 5: Markdown形式での生成**
（逆時系列、見出し・箇条書き・太字の活用）

#### 履歴書データとの統合

職務経歴書生成時、履歴書データ（YAML/JSON）を同時に受け取った場合：
1. `personal_info`（氏名、生年月日、電話、メール）を自動抽出
2. `qualifications`（免許・資格）を自動抽出
3. これらをPDFヘッダーに配置（ユーザーはMarkdown本文に記述不要）
```

---

## 実装順序とマイルストーン

### Phase 0: 構造再編（別PR）

**対応内容:**
- Agent Skills標準構造への再編（scripts/, references/, assets/）
- 既存コードのパス参照修正
- ビルドスクリプトの修正

**影響範囲:** 既存のすべてのファイル

### Phase 1: ベストプラクティスリソース作成 ✅ 完了

**対応内容:**
- `references/career_sheet_best_practices.md` の作成
- PREP法、STAR法、優秀者向けTipsの記述

**テスト:** ドキュメントレビュー

**完了日**: 2025-12-30

### Phase 2: スキーマ設計

**対応内容:**
- `assets/schemas/career_sheet_schema.json` の作成
- `assets/examples/sample_career_sheet.yaml` の作成

**テスト:** JSON Schemaバリデーション

### Phase 3: Markdown変換実装

**対応内容:**
- `scripts/jtr/markdown_to_richtext.py` の実装
- ユニットテスト作成

**カバレッジ目標:** 80%以上

### Phase 4: PDF生成実装

**対応内容:**
- `scripts/jtr/career_sheet_generator.py` の実装
- 統合テスト作成

**カバレッジ目標:** 80%以上

### Phase 5: エントリーポイント統合

**対応内容:**
- `scripts/main.py` の更新（document_type分岐追加）
- `scripts/jtr/__init__.py` の更新（新規関数エクスポート）

**テスト:** エンドツーエンドテスト

### Phase 6: SKILL.md更新

**対応内容:**
- `SKILL.md` への職務経歴書セクション追加
- LLM向け指示の明確化

**テスト:** ドキュメントレビュー

### Phase 7: ドキュメント更新

**対応内容:**
- `AGENTS.md` の機能要件更新
- `docs/specifications.md` の技術仕様追加
- `references/README.md` のエンドユーザー向けガイド更新

---

## テスト戦略

### カバレッジ要件

**必須**: 全体カバレッジ80%以上（CI/CDで強制）

### テストケース分類

#### 1. ユニットテスト

**対象:**
- `markdown_to_richtext.py`: Markdown構文変換
- `career_sheet_generator.py`: PDF生成ロジック

**カバレッジ:** 各モジュール80%以上

#### 2. 統合テスト

**対象:**
- 履歴書データとの統合（個人情報・資格の自動抽出）
- エンドツーエンドのPDF生成

**シナリオ:**
- 基本的な職務経歴書生成
- 履歴書データ参照あり/なし
- カスタムフォント使用

#### 3. 異常系テスト

**シナリオ:**
- 不正なスキーマ
- 不正なMarkdown構文
- フォントファイル不足

---

## セキュリティ考慮事項

### 入力サニタイゼーション

- Markdown内のHTML/JavaScriptは無害化（reportlabが自動エスケープ）
- ファイルパスのバリデーション（パストラバーサル対策）

### 機密情報の扱い

- PDFに機密情報（APIキー等）を含めない
- ユーザー入力の適切な検証

---

## パフォーマンス考慮事項

### PDF生成時間

- 目標: 3秒以内（A4 2-3ページ想定）
- Markdown変換の最適化（大量テキスト対応）

### メモリ使用量

- reportlabのFlowable生成を効率化
- 大量データ時のストリーミング処理検討（将来）

---

## 将来拡張

### Phase 8以降（検討事項）

1. **Markdown構文の拡張**
   - 表（テーブル）対応
   - リンク対応
   - コードブロック対応

2. **テンプレートの追加**
   - 業種別テンプレート（IT、営業、クリエイティブ等）
   - デザインバリエーション（色、レイアウト）

3. **ATS対応**
   - キーワード最適化
   - パーサブルなPDF形式

4. **国際化**
   - 英語版職務経歴書（Resume/CV）対応

---

## 参考資料

### Web調査結果

- [職務経歴書の書き方マニュアル](https://tenshoku.mynavi.jp/knowhow/sample/)
- [2025年最新 職務経歴書の書き方完全ガイド](https://career-navi.pair-agent.com/resume-writing-complete-guide-2025/)
- [職務経歴書レイアウト・デザインの基本](https://syokumu-keirekisyo.formmaker.jp/shokumukeirekisho-layout-design)
- [職務経歴書フォーマット無料ダウンロード](https://next.rikunabi.com/tenshokuknowhow/shokurekisho/template/)

### 人事からのアドバイス

- PREP法、STAR法、SDS法の活用
- 逆時系列と数値化の徹底
- 戦略的カスタマイズ（応募企業への最適化80%以上）
- 優秀者向けTips（手抜き上手、完璧主義を避ける）

---

## 承認とレビュー

この設計ドキュメントは以下のレビューを経て承認されます：

- [ ] アーキテクチャレビュー
- [ ] セキュリティレビュー
- [ ] テスト戦略レビュー
- [ ] ドキュメントレビュー

承認後、Phase 0（構造再編）から順次実装を開始します。
