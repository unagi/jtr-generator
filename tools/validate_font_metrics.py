"""
フォントメトリクス検証スクリプト

BIZ UDMinchoフォントの実際のメトリクス値を取得し、
氏名フィールドの理論的なbaseline位置を計算する。
"""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def main():
    # フォント登録
    base_dir = Path(__file__).parent.parent
    font_path = base_dir / "fonts/BIZ_UDMincho/BIZUDMincho-Regular.ttf"

    if not font_path.exists():
        print(f"Error: Font file not found at {font_path}")
        return

    pdfmetrics.registerFont(TTFont("BIZUDMincho-Regular", str(font_path)))

    # メトリクス取得
    font = pdfmetrics.getFont("BIZUDMincho-Regular")
    ascent = font.face.ascent
    descent = font.face.descent

    print("=" * 60)
    print("BIZ UDMincho Regular - Font Metrics")
    print("=" * 60)
    print(f"Ascent:  {ascent:6.0f} (1000em units)")
    print(f"Descent: {descent:6.0f} (1000em units)")
    print()

    # 28ptでの実際の値
    font_size = 28.0
    ascent_pt = ascent * (font_size / 1000)
    descent_pt = descent * (font_size / 1000)
    text_height = ascent_pt - descent_pt  # descentは負値なので減算

    print(f"At {font_size}pt:")
    print(f"  Ascent:      {ascent_pt:6.2f}pt")
    print(f"  Descent:     {descent_pt:6.2f}pt")
    print(f"  Text height: {text_height:6.2f}pt")
    print()

    # セル情報（氏名フィールド）
    cell_top = 718.94  # ふりがなと氏名の間の罫線
    cell_bottom = 633.5  # 日生の上の罫線
    cell_height = cell_top - cell_bottom
    cell_center = (cell_top + cell_bottom) / 2

    print("Cell Information (Name Field):")
    print(f"  Top:      {cell_top:6.2f}pt")
    print(f"  Bottom:   {cell_bottom:6.2f}pt")
    print(f"  Height:   {cell_height:6.2f}pt")
    print(f"  Center:   {cell_center:6.2f}pt")
    print()

    # 理論的なbaseline位置の計算
    # テキストの視覚的中心 = baseline + (ascent_pt + descent_pt) / 2
    # これをcell_centerに一致させる
    text_visual_center_offset = (ascent_pt + descent_pt) / 2
    baseline_calculated = cell_center - text_visual_center_offset

    print("Baseline Calculation:")
    print(f"  Text visual center offset: {text_visual_center_offset:6.2f}pt")
    print(f"  Calculated baseline:       {baseline_calculated:6.2f}pt")
    print()

    # 現在の位置との比較
    current_baseline = 666.0
    diff = baseline_calculated - current_baseline

    print("Comparison with Current Position:")
    print(f"  Current baseline:  {current_baseline:6.2f}pt")
    print(f"  Calculated:        {baseline_calculated:6.2f}pt")
    print(f"  Difference:        {diff:+6.2f}pt")
    print()

    # 視覚的な位置の確認
    current_text_top = current_baseline + ascent_pt
    current_text_bottom = current_baseline + descent_pt

    calculated_text_top = baseline_calculated + ascent_pt
    calculated_text_bottom = baseline_calculated + descent_pt

    print("Visual Position Comparison:")
    print("  Current:")
    print(f"    Text top:    {current_text_top:6.2f}pt")
    print(f"    Text bottom: {current_text_bottom:6.2f}pt")
    print(f"    Text center: {(current_text_top + current_text_bottom) / 2:6.2f}pt")
    print()
    print("  Calculated:")
    print(f"    Text top:    {calculated_text_top:6.2f}pt")
    print(f"    Text bottom: {calculated_text_bottom:6.2f}pt")
    print(f"    Text center: {(calculated_text_top + calculated_text_bottom) / 2:6.2f}pt")
    print()

    # 評価
    print("=" * 60)
    print("Evaluation:")
    print("=" * 60)
    if abs(diff) < 1.0:
        print(f"✅ 差分は{abs(diff):.2f}ptで、視覚的に無視できる範囲です。")
        print("   現在の位置で十分に正確です。")
    elif abs(diff) < 3.0:
        print(f"⚠️  差分は{abs(diff):.2f}ptで、微細なズレがあります。")
        print("   改善の余地がありますが、実用上は問題ないレベルです。")
    else:
        print(f"❌ 差分は{abs(diff):.2f}ptで、視覚的に目立つ可能性があります。")
        print("   フォントメトリクスベースの計算を推奨します。")
    print()


if __name__ == "__main__":
    main()
