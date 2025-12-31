"""Tests for skill.scripts.jtr.layout.metrics module"""

from pathlib import Path

import pytest

# reportlabがない環境ではスキップ
pytest.importorskip("reportlab")

from skill.scripts.jtr.layout.metrics import get_font_metrics, register_font


class TestRegisterFont:
    """register_font関数のテスト（再エクスポート確認）"""

    def test_register_font_success(self) -> None:
        """フォント登録が成功することを確認"""
        # デフォルトフォントを使用（BIZ UDMincho）
        from skill.scripts.jtr.helper.fonts import find_default_font

        font_path = find_default_font()
        font_name = register_font(font_path)

        assert font_name == font_path.stem
        assert font_name  # 空でないことを確認

    def test_register_font_not_found(self, tmp_path: Path) -> None:
        """存在しないフォントパスでFileNotFoundErrorが発生"""
        non_existent = tmp_path / "non_existent.ttf"

        with pytest.raises(FileNotFoundError, match="フォントファイルが見つかりません"):
            register_font(non_existent)


class TestGetFontMetrics:
    """get_font_metrics関数のテスト"""

    def test_get_font_metrics_basic(self) -> None:
        """基本的なフォントメトリクスの取得"""
        # まずフォントを登録
        from skill.scripts.jtr.helper.fonts import find_default_font

        font_path = find_default_font()
        font_name = register_font(font_path)

        # メトリクスを取得
        metrics = get_font_metrics(font_name, 12.0)

        # 必須フィールドの存在確認
        assert "ascent" in metrics
        assert "descent" in metrics
        assert "height" in metrics

        # 型確認
        assert isinstance(metrics["ascent"], float)
        assert isinstance(metrics["descent"], float)
        assert isinstance(metrics["height"], float)

        # 値の妥当性確認
        assert metrics["ascent"] > 0  # 上昇値は正
        assert metrics["descent"] < 0  # 下降値は負
        assert metrics["height"] > 0  # 高さは正
        assert metrics["height"] == metrics["ascent"] - metrics["descent"]

    def test_get_font_metrics_different_sizes(self) -> None:
        """異なるフォントサイズでメトリクスが変化することを確認"""
        from skill.scripts.jtr.helper.fonts import find_default_font

        font_path = find_default_font()
        font_name = register_font(font_path)

        metrics_12 = get_font_metrics(font_name, 12.0)
        metrics_24 = get_font_metrics(font_name, 24.0)

        # サイズ24はサイズ12のほぼ2倍
        assert metrics_24["height"] > metrics_12["height"]
        assert metrics_24["ascent"] > metrics_12["ascent"]
        # descentは負なので、24の方が絶対値が大きい（より負）
        assert metrics_24["descent"] < metrics_12["descent"]

    def test_get_font_metrics_unregistered_font(self) -> None:
        """未登録フォントでエラーが発生することを確認"""
        # ReportLabがKeyErrorを投げる
        with pytest.raises(KeyError):
            get_font_metrics("NonExistentFont", 12.0)
