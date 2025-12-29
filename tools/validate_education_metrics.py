"""
学歴・職歴フィールドのフォントメトリクス検証

11ptフォントでの理論的baseline位置を計算する。
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
    print("BIZ UDMincho Regular - Font Metrics (Education/Work History)")
    print("=" * 60)

    # 11ptでの実際の値
    font_size = 11.0
    ascent_pt = ascent * (font_size / 1000)
    descent_pt = descent * (font_size / 1000)
    text_height = ascent_pt - descent_pt

    print(f"At {font_size}pt:")
    print(f"  Ascent:      {ascent_pt:6.2f}pt")
    print(f"  Descent:     {descent_pt:6.2f}pt")
    print(f"  Text height: {text_height:6.2f}pt")
    print()

    # セル情報（学歴・職歴セクション）
    # タイトル行: 763.66 - 741.94（高さ約21pt）
    # データ行1: 740.98 - 716.14（高さ約25pt、二重線1pt含む）
    # データ行2: 715.18 - 690.34（高さ約25pt）
    # ...

    # データ行の実質的な高さ: 24.84pt
    row_height = 24.84

    print("Education/Work History Section Analysis:")
    print()
    print(f"  Row height:  {row_height:.2f}pt")
    print(f"  Font size:   {font_size}pt")
    print()

    # 各行のbaseline位置を計算
    # 行の上端と下端を定義
    row_tops = [740.98, 715.18, 689.38, 663.58, 637.78, 611.98]
    row_bottoms = [716.14, 690.34, 664.54, 638.74, 612.94, 587.10]

    print("Baseline Calculation for each row:")
    print()

    for i, (top, bottom) in enumerate(zip(row_tops, row_bottoms, strict=True)):
        cell_center = (top + bottom) / 2
        text_visual_center_offset = (ascent_pt + descent_pt) / 2
        baseline_calculated = cell_center - text_visual_center_offset

        print(f"Row {i+1}:")
        print(f"  Top:         {top:.2f}pt")
        print(f"  Bottom:      {bottom:.2f}pt")
        print(f"  Center:      {cell_center:.2f}pt")
        print(f"  Baseline:    {baseline_calculated:.2f}pt")
        print()

    # 列のX座標
    print("Column X coordinates:")
    print(f"  Year column center:   {(54.49 + 109.21) / 2:.2f}pt")
    print(f"  Month column center:  {(109.33 + 135.01) / 2:.2f}pt")
    print(f"  Content start:        {135.97 + 5:.2f}pt (5pt padding)")
    print()


if __name__ == "__main__":
    main()
