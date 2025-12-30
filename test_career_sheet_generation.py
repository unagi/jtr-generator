#!/usr/bin/env python3
"""職務経歴書PDF生成の手動テストスクリプト"""

from pathlib import Path

# skill/scripts をパスに追加
import sys
sys.path.insert(0, str(Path(__file__).parent / "skill" / "scripts"))

from main import main

# サンプルファイルのパス
sample_resume = Path("skill/assets/examples/sample_resume.yaml")
sample_markdown = Path("skill/assets/examples/sample_career_content.md")
sample_additional = Path("skill/assets/examples/sample_additional_info.yaml")

# 出力先
output_path = Path("outputs/test_career_sheet.pdf")
output_path.parent.mkdir(exist_ok=True)

print("職務経歴書PDF生成テスト")
print(f"履歴書データ: {sample_resume}")
print(f"Markdown: {sample_markdown}")
print(f"追加情報: {sample_additional}")
print(f"出力先: {output_path}")
print()

try:
    result_path = main(
        input_data=sample_resume,
        document_type="career_sheet",
        markdown_content=sample_markdown,
        additional_info=sample_additional,
        output_path=output_path,
    )
    print(f"✅ 職務経歴書PDFを生成しました: {result_path}")
    print(f"   ファイルサイズ: {result_path.stat().st_size:,} bytes")
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
