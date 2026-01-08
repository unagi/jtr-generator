# A4サイズレイアウトデータ

## ディレクトリ構成

```
data/a4/
├── rirekisho_layout.json              # 最終レイアウトデータ（配布必須）
├── definitions/
│   └── manual_bounds.json          # 手動測定した境界座標
│   └── career_sheet_manual_bounds.json    # 職務経歴書の手動測定境界
└── rules/
    ├── label_alignment.json        # 固定ラベルの配置ルール
    ├── field_alignment.json        # データフィールドの配置ルール
    ├── career_sheet_spacing.json   # 職務経歴書の余白・インデント定義
    └── career_sheet_label_alignment.json  # 職務経歴書ラベル配置ルール
```

## rirekisho_layout.json

JIS規格履歴書（A4 x 2ページ）の最終レイアウトデータ（v4フォーマット）。

### データ構造

```json
{
  "source_page_size_pt": [1190.52, 841.92],  // 参照PDFサイズ（A3横）
  "split_x_pt": 595.26,                      // 左右分割点（A4幅）
  "page1_lines": [...],                       // ページ1の罫線（107本）
  "page2_lines": [...],                       // ページ2の罫線（101本）
  "page1_texts": [...],                       // ページ1の固定ラベル（24個）
  "page2_texts": [...]                        // ページ2の固定ラベル（9個）
}
```

### 構成要素

#### 罫線（lines）

合計: **208本**（Page 1: 107本、Page 2: 101本）

各罫線の属性:
- `x0`, `y0`, `x1`, `y1`: 始点・終点座標（pt、ReportLab座標系）
- `width`: 線幅（pt）
- `dash_pattern`: 破線パターン（空配列=実線）
- `dash_phase`: 破線の開始位置
- `cap`: 線端のスタイル（2=丸）
- `join`: 線結合スタイル（1=マイター）
- `color`: RGB色（[0.0, 0.0, 0.0]=黒）

#### 固定テキストラベル（texts）

合計: **33個**（Page 1: 24個、Page 2: 9個）

各テキストの属性:
- `text`: 表示内容（例: "履　歴　書"、"氏　　名"、"ふりがな"）
- `x`, `y`: 座標（pt、ReportLab座標系、ベースライン左端）
- `font_size`: フォントサイズ（pt）
- `align`: 配置方向（"left", "center", "right"）

**主な固定ラベル:**
- Page 1: "履歴書"、"氏名"、"ふりがな"×3、"現住所"、"連絡先"、"学歴・職歴"、写真エリア説明文、注記等
- Page 2: "学歴・職歴"、"免許・資格"、"志望の動機"、"本人希望記入欄"等

### 座標系

- **原点**: 左下（ReportLab座標系）
- **単位**: pt（ポイント、1pt = 1/72 inch）
- **Y軸**: 下から上へ増加

#### 参照PDFからの変換

参照PDF（`tests/fixtures/R3_pdf_rirekisyo.pdf`）はA3横（1190.52×841.92pt）の1ページ構成。
これを595.26ptで左右分割し、A4 x 2ページに変換。

**座標変換式:**

```python
# PyMuPDF（左上原点、Y軸下向き）→ ReportLab（左下原点、Y軸上向き）
page_height_pt = 841.92
y_reportlab = page_height_pt - y_pymupdf

# ページ2（右半分）のX座標オフセット
split_x_pt = 595.26
x_page2 = x_original - split_x_pt
```

### 生成方法

#### Phase 1: 罫線抽出

```bash
uv run python tools/extract_lines.py
```

出力: `data/extracted_lines.json`（208本の罫線定義）

#### Phase 2: テキスト抽出

```bash
# 全テキストの抽出（手動選別前）
uv run python tools/extract_text_positions.py
# → data/extracted_texts_raw.json

# 固定ラベルの包括的抽出
uv run python tools/extract_all_missing_texts.py
# → data/extracted_all_labels.json
```

**手動選別:**
- 記入済みデータ（氏名、住所、電話番号等）を除外
- 固定ラベルのみを抽出
- 出力: `data/extracted_texts_labels_only.json`

#### Phase 3: レイアウト統合

```bash
uv run python tools/merge_text_to_layout.py
```

出力: `data/a4/rirekisho_layout.json`（最終版）

### 視覚品質（Phase 4e完了時）

#### 測定条件

- **参照PDF**: `tests/fixtures/R3_pdf_rirekisyo.pdf`（記入済み履歴書）
- **生成PDF**: ブランク履歴書（固定ラベル付き、罫線のみ）
- **測定解像度**: 300dpi
- **比較手法**: SSIM（構造類似度）、ピクセル差異率（threshold=5）

#### スコア

| 指標 | Page 1 | Page 2 | 平均 |
|------|--------|--------|------|
| **SSIM** | 0.900 | 0.909 | **0.905** |
| **Pixel Diff** | 5.98% | 5.36% | **5.67%** |

**テスト閾値（Phase 5: オプション2 - 厳格）:**
- SSIM: > 0.895（マージン -0.01）
- Pixel Diff: < 6.0%（マージン +0.33%）

#### 差異の内訳

完全一致にならない理由:

1. **フォント差異（約0.5%）**
   - 参照PDF: MS-Mincho（埋め込みフォント）
   - 生成PDF: BIZ UDMincho Regular
   - 字幅・太さの微妙な違い

2. **記入済みデータ（約2.5%）**
   - 参照PDFの氏名、住所、電話番号、学歴、職歴等
   - ブランク履歴書では空欄

3. **アンチエイリアシング（約0.3%）**
   - レンダリングエンジンの違い
   - threshold=5で大部分は吸収済み

4. **浮動小数点誤差（約0.1%）**
   - 座標計算の丸め誤差

**結論:** 現在のスコア（SSIM 0.905、Diff 5.67%）は**ブランク履歴書として妥当な品質**に到達。

### 到達可能な最良スコア

フォント・レンダリングの限界により、以下が到達可能な最良値:

- **SSIM**: 0.91-0.92
- **Pixel Diff**: 3.0-3.5%（記入済みデータ除外不可）

これ以上の改善は参照PDFと同一フォントを使用しない限り困難。

### Phase 4: レイアウト検証

#### 検証データフロー

```
[入力]
├── rirekisho_layout.json              ← 検証対象の最終レイアウトデータ
├── definitions/manual_bounds.json  ← 手動測定した境界座標（写真エリア、満〇歳セル）
└── rules/*.json                    ← 配置ルール定義（align/valign/margin）

[検証ツール]
├── tools/layout/analyze_text_alignment.py        ← 固定ラベルの配置検証
└── tools/layout/analyze_data_field_alignment.py  ← データフィールドの配置検証

[出力]
└── outputs/validation/
    ├── label_alignment_report.json    ← 固定ラベルの検証レポート
    └── field_alignment_report.json    ← データフィールドの検証レポート
```

#### 検証コマンド

```bash
# 固定ラベルの配置検証
uv run python tools/layout/analyze_text_alignment.py

# データフィールドの配置検証
uv run python tools/layout/analyze_data_field_alignment.py
```

#### 検証ファイルの役割

**definitions/manual_bounds.json:**
- 写真エリア・満〇歳セルなど、罫線から計算できない特殊セルの境界座標
- ルールベースの計算では求められない実測値を定義

**rules/label_alignment.json:**
- 固定ラベルの配置ルール（align/valign、margin、bounds指定）
- フォントメトリクスと組み合わせて期待座標を計算

**rules/field_alignment.json:**
- データフィールドの配置ルール（align/valign、margin）
- page1_fields、multiline_blocks、dynamic_rowsの定義

#### 検証履歴（2025-12-29）

- **Phase 4a**: セル単位比較ツール実装
- **Phase 4b**: 写真エリア・満〇歳セルのテキスト抽出
- **Phase 4c**: セル単位再測定（写真エリア: 6要素追加）
- **Phase 4d**: 満〇歳セルの全角・半角スペース混在対応
- **Phase 4e**: 包括的な不足ラベル抽出（Page 1: +6個、Page 2: +3個）
- **修正**: （満　歳）の二重描画を解消

詳細: `outputs/adjustment_log.md`

#### Phase 5: テスト閾値再設定・ドキュメント化（2025-12-29）

- **Phase 5-1**: テスト閾値の再設定（オプション2採用）
- **Phase 5-2**: 本READMEの作成
- **Phase 5-3**: 一時ファイルの整理
- **Phase 5-4**: 全テストの実行と動作確認

### 使用方法

#### PDF生成

```python
from pathlib import Path
from skill.scripts.jtr.rirekisho_generator import generate_rirekisho_pdf

output_path = Path("outputs/rirekisho.pdf")
generate_rirekisho_pdf({}, {"paper_size": "A4"}, output_path)
```

出力: JIS規格準拠のブランク履歴書（A4 x 2ページ、固定ラベル付き）

#### 視覚テスト

```bash
# ピクセル差異率 + SSIM
uv run pytest tests/generators/test_pdf_visual.py -v

# デバッグ画像生成（差分可視化）
uv run pytest tests/generators/test_pdf_visual.py::test_save_diff_image_for_debugging -v
# → outputs/debug/diff_page1.png, diff_page2.png
```

### スキーマ定義

JSONスキーマ: `tools/schema/layout_schema.json`

バリデーション:
```bash
uv run python -c "
import json
import jsonschema

with open('tools/schema/layout_schema.json') as f:
    schema = json.load(f)

with open('skill/assets/data/a4/rirekisho_layout.json') as f:
    layout = json.load(f)

jsonschema.validate(layout, schema)
print('✅ スキーマバリデーション成功')
"
```

### 関連ドキュメント

- **プロジェクト概要**: `README.md`
- **調整履歴**: `outputs/adjustment_log.md`
- **JSONスキーマ**: `tools/schema/layout_schema.json`
- **参照PDF**: `tests/fixtures/R3_pdf_rirekisyo.pdf`

### ライセンス

MIT License - 詳細は `LICENSE` を参照。
