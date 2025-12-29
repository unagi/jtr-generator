# フォントディレクトリ

このディレクトリには、履歴書PDF生成に使用するTrueTypeフォント（.ttf）を配置します。

## 配置方法

1. **フォントファイルを入手**
   - ライセンスを確認し、商用利用可能なフォントを選択してください
   - 推奨：M+ FONTS、Noto Sans JP、IPAフォント等

2. **このディレクトリに配置**
   ```bash
   cp /path/to/your/font.ttf fonts/
   ```

3. **config.yamlで指定**
   ```yaml
   fonts:
     main: fonts/your-font.ttf
     heading: fonts/your-heading-font.ttf  # optional
   ```

## 注意事項

- **このディレクトリのフォントファイルはgit管理外です**（.gitignoreに設定済み）
- ライセンス上の理由により、フォントファイルは同梱していません
- ユーザー自身でライセンスを確認の上、配置してください

## サンプル設定

### M+ 1p Regular の例

1. M+ FONTSを公式サイトからダウンロード
2. `mplus-1p-regular.ttf` をこのディレクトリに配置
3. config.yamlで指定:

```yaml
fonts:
  main: fonts/mplus-1p-regular.ttf
```

詳細は[プロジェクトドキュメント](../AGENTS.md)を参照してください。
