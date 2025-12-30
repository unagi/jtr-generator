# フォントディレクトリ

このディレクトリには、履歴書PDF生成に使用するTrueTypeフォント（.ttf）を配置します。

## デフォルトフォント（BIZ UDMincho）

v0.1.0以降、BIZ UDMincho Regular がデフォルトフォントとして同梱されています。

- **場所**: `fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf`
- **ライセンス**: SIL Open Font License 1.1（`fonts/BIZ_UDMincho/OFL.txt`参照）
- **用途**: `options['fonts']` 未指定時に自動的に使用されます

### なぜこのフォントを選んだか

- **ライセンス**: OFL 1.1により再配布が明示的に許可されている
- **視覚的品質**: JIS規格の履歴書参照PDFとの構造類似度（SSIM）が高い（0.908913）
- **ユニバーサルデザイン**: 可読性に優れ、公的書類に適している
- **商用利用可能**: 企業での履歴書生成にも安心して使用できる
- **ファイルサイズ**: 5.7MBと比較的コンパクト

## カスタムフォントの配置

デフォルトフォント以外を使用する場合は、以下の手順でカスタムフォントを配置できます。

### 配置方法

1. **フォントファイルを入手**
   - ライセンスを確認し、商用利用可能なフォントを選択してください
   - 推奨：M+ FONTS、Noto Sans JP、IPAフォント等

2. **このディレクトリに配置**
   ```bash
   mkdir -p fonts/custom
   cp /path/to/your/font.ttf fonts/custom/
   ```

3. **config.yamlで指定**
   ```yaml
   fonts:
     main: fonts/custom/your-font.ttf
     heading: fonts/custom/your-heading-font.ttf  # optional
   ```

## 注意事項

- **BIZ_UDMincho/ 以外のフォントファイルはgit管理外です**（.gitignoreに設定済み）
- カスタムフォントを使用する場合、ライセンスを確認の上、配置してください
- デフォルトフォント（BIZ_UDMincho/）は git 管理対象です

詳細は[プロジェクトドキュメント](../AGENTS.md)を参照してください。
