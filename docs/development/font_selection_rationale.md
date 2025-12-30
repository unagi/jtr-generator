# フォント選定の根拠

**作成日**: 2025-12-29

## 検証条件

- **参照PDF**: `tests/fixtures/R3_pdf_rirekisyo.pdf`
- **サンプルテキスト**: 山田太郎、東京都渋谷区神南1-1-1 等
- **解像度**: 300dpi
- **評価指標**: SSIM（構造類似度）

## 検証結果

| フォント | SSIM |
|---------|------|
| BIZ UDMincho Regular | **0.908913** |
| BIZ UDMincho Bold    | 0.908138 |

**差**: 0.000775（0.01未満の僅差）

## 選定基準

SSIM差が僅少（< 0.01）のため、以下の追加基準で判断:

1. **可読性**: Regular体の方が履歴書として標準的
2. **汎用性**: 公的文書では太字より標準ウェイトが一般的
3. **印刷適性**: Bold体は印刷時にインク消費が多い

## 結論

**BIZ UDMincho Regular** を採用

- 視覚品質: 参照PDFとほぼ同等（SSIM 0.909）
- 実用性: 履歴書の標準フォントとして適切
- 互換性: ユニバーサルデザインフォント（視認性向上）

## 参考

- BIZ UDフォント: https://github.com/googlefonts/morisawa-biz-ud-mincho
- ライセンス: SIL Open Font License 1.1
