"""skill.scripts.jtr.layout.anchors モジュールのテスト"""

import pytest
from jtr.layout.anchors import (
    _cluster_positions,
    _collect_line_positions,
    _nearest_position,
    build_text_anchors,
    resolve_texts_from_anchors,
)


class TestClusterPositions:
    """_cluster_positions関数のテスト"""

    def test_empty_list(self) -> None:
        """空のリストを渡すと空のリストが返る"""
        assert _cluster_positions([], tol=0.5) == []

    def test_single_value(self) -> None:
        """単一の値を渡すとそのまま返る"""
        assert _cluster_positions([100.0], tol=0.5) == [100.0]

    def test_cluster_within_tolerance(self) -> None:
        """許容範囲内の値は1つのクラスタにまとめられる"""
        result = _cluster_positions([100.0, 100.2, 100.4], tol=0.5)
        assert len(result) == 1
        assert abs(result[0] - 100.2) < 0.01  # 平均値

    def test_multiple_clusters(self) -> None:
        """許容範囲外の値は別のクラスタに分けられる"""
        result = _cluster_positions([100.0, 100.2, 200.0, 200.3], tol=0.5)
        assert len(result) == 2
        assert abs(result[0] - 100.1) < 0.01
        assert abs(result[1] - 200.15) < 0.01

    def test_unsorted_input(self) -> None:
        """未ソートの入力でも正しくクラスタリングされる"""
        result = _cluster_positions([200.0, 100.0, 100.3], tol=0.5)
        assert len(result) == 2
        assert result[0] < result[1]  # ソート済み


class TestCollectLinePositions:
    """_collect_line_positions関数のテスト"""

    def test_invalid_axis(self) -> None:
        """不正な軸指定でValueErrorが発生"""
        lines = [{"x0": 10, "y0": 20, "x1": 10, "y1": 100}]
        with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
            _collect_line_positions(lines, axis="z", tol=0.5)

    def test_collect_vertical_lines(self) -> None:
        """垂直線（x軸）の座標を収集"""
        lines = [
            {"x0": 10.0, "y0": 20, "x1": 10.0, "y1": 100},  # 垂直線
            {"x0": 10.2, "y0": 30, "x1": 10.2, "y1": 90},  # 垂直線
            {"x0": 10.0, "y0": 50, "x1": 100.0, "y1": 50},  # 水平線（除外）
        ]
        result = _collect_line_positions(lines, axis="x", tol=0.5)
        assert len(result) == 1  # 2本の垂直線がクラスタリングされる
        assert abs(result[0] - 10.1) < 0.01

    def test_collect_horizontal_lines(self) -> None:
        """水平線（y軸）の座標を収集"""
        lines = [
            {"x0": 10, "y0": 50.0, "x1": 100, "y1": 50.0},  # 水平線
            {"x0": 20, "y0": 50.3, "x1": 80, "y1": 50.3},  # 水平線
            {"x0": 30.0, "y0": 20, "x1": 30.0, "y1": 100},  # 垂直線（除外）
        ]
        result = _collect_line_positions(lines, axis="y", tol=0.5)
        assert len(result) == 1
        assert abs(result[0] - 50.15) < 0.01

    def test_empty_lines(self) -> None:
        """空の罫線リストを渡すと空のリストが返る"""
        assert _collect_line_positions([], axis="x", tol=0.5) == []


class TestNearestPosition:
    """_nearest_position関数のテスト"""

    def test_no_positions(self) -> None:
        """空の位置リストでValueErrorが発生"""
        with pytest.raises(ValueError, match="No line positions found"):
            _nearest_position(100.0, [])

    def test_exact_match(self) -> None:
        """完全一致する位置が返る"""
        positions = [50.0, 100.0, 150.0]
        assert _nearest_position(100.0, positions) == 100.0

    def test_nearest_below(self) -> None:
        """最も近い位置（下側）が返る"""
        positions = [50.0, 100.0, 150.0]
        assert _nearest_position(95.0, positions) == 100.0

    def test_nearest_above(self) -> None:
        """最も近い位置（上側）が返る"""
        positions = [50.0, 100.0, 150.0]
        assert _nearest_position(105.0, positions) == 100.0

    def test_single_position(self) -> None:
        """位置が1つだけの場合"""
        positions = [100.0]
        assert _nearest_position(200.0, positions) == 100.0


class TestBuildTextAnchors:
    """build_text_anchors関数のテスト"""

    def test_basic_anchor_generation(self) -> None:
        """基本的なアンカー生成"""
        texts = [
            {"text": "氏名", "x": 10.1, "y": 50.2, "font_size": 10, "align": "left"},
        ]
        lines = [
            {"x0": 10.0, "y0": 20, "x1": 10.0, "y1": 100},  # 垂直線
            {"x0": 5, "y0": 50.0, "x1": 100, "y1": 50.0},  # 水平線
        ]

        result = build_text_anchors(texts, lines, tol=0.5)

        assert len(result) == 1
        anchor = result[0]
        assert anchor["text"] == "氏名"
        assert anchor["font_size"] == 10
        assert anchor["align"] == "left"
        assert anchor["anchor"]["x_line"] == 10.0
        assert anchor["anchor"]["y_line"] == 50.0
        assert abs(anchor["offset"]["dx"] - 0.1) < 0.01
        assert abs(anchor["offset"]["dy"] - 0.2) < 0.01
        assert anchor["reference_position"]["x"] == 10.1
        assert anchor["reference_position"]["y"] == 50.2

    def test_default_align(self) -> None:
        """alignが省略された場合のデフォルト値"""
        texts = [{"text": "テスト", "x": 10.0, "y": 50.0, "font_size": 12}]
        lines = [
            {"x0": 10.0, "y0": 20, "x1": 10.0, "y1": 100},
            {"x0": 5, "y0": 50.0, "x1": 100, "y1": 50.0},
        ]

        result = build_text_anchors(texts, lines)
        assert result[0]["align"] == "left"

    def test_multiple_texts(self) -> None:
        """複数テキストのアンカー生成"""
        texts = [
            {"text": "氏名", "x": 10.0, "y": 50.0, "font_size": 10},
            {"text": "住所", "x": 10.0, "y": 100.0, "font_size": 10},
        ]
        lines = [
            {"x0": 10.0, "y0": 0, "x1": 10.0, "y1": 200},
            {"x0": 0, "y0": 50.0, "x1": 100, "y1": 50.0},
            {"x0": 0, "y0": 100.0, "x1": 100, "y1": 100.0},
        ]

        result = build_text_anchors(texts, lines)
        assert len(result) == 2
        assert result[0]["text"] == "氏名"
        assert result[1]["text"] == "住所"

    def test_empty_inputs(self) -> None:
        """空のテキスト/罫線リストの場合"""
        assert build_text_anchors([], []) == []


class TestResolveTextsFromAnchors:
    """resolve_texts_from_anchors関数のテスト"""

    def test_basic_resolution(self) -> None:
        """基本的なアンカー解決"""
        anchors = [
            {
                "text": "氏名",
                "font_size": 10,
                "align": "left",
                "anchor": {"x_line": 10.0, "y_line": 50.0},
                "offset": {"dx": 0.5, "dy": 1.0},
            },
        ]
        lines = [
            {"x0": 10.0, "y0": 20, "x1": 10.0, "y1": 100},
            {"x0": 5, "y0": 50.0, "x1": 100, "y1": 50.0},
        ]

        result = resolve_texts_from_anchors(anchors, lines)

        assert len(result) == 1
        resolved = result[0]
        assert resolved["text"] == "氏名"
        assert resolved["font_size"] == 10
        assert resolved["align"] == "left"
        assert abs(resolved["x"] - 10.5) < 0.01
        assert abs(resolved["y"] - 51.0) < 0.01

    def test_default_align_in_resolution(self) -> None:
        """alignが省略された場合のデフォルト値（解決時）"""
        anchors = [
            {
                "text": "テスト",
                "font_size": 12,
                "anchor": {"x_line": 10.0, "y_line": 50.0},
                "offset": {"dx": 0.0, "dy": 0.0},
            },
        ]
        lines = [
            {"x0": 10.0, "y0": 20, "x1": 10.0, "y1": 100},
            {"x0": 5, "y0": 50.0, "x1": 100, "y1": 50.0},
        ]

        result = resolve_texts_from_anchors(anchors, lines)
        assert result[0]["align"] == "left"

    def test_multiple_anchors(self) -> None:
        """複数アンカーの解決"""
        anchors = [
            {
                "text": "氏名",
                "font_size": 10,
                "anchor": {"x_line": 10.0, "y_line": 50.0},
                "offset": {"dx": 0.0, "dy": 0.0},
            },
            {
                "text": "住所",
                "font_size": 10,
                "anchor": {"x_line": 10.0, "y_line": 100.0},
                "offset": {"dx": 0.0, "dy": 0.0},
            },
        ]
        lines = [
            {"x0": 10.0, "y0": 0, "x1": 10.0, "y1": 200},
            {"x0": 0, "y0": 50.0, "x1": 100, "y1": 50.0},
            {"x0": 0, "y0": 100.0, "x1": 100, "y1": 100.0},
        ]

        result = resolve_texts_from_anchors(anchors, lines)
        assert len(result) == 2
        assert result[0]["text"] == "氏名"
        assert result[1]["text"] == "住所"

    def test_empty_anchors(self) -> None:
        """空のアンカーリストの場合"""
        assert resolve_texts_from_anchors([], []) == []

    def test_nearest_position_snapping(self) -> None:
        """最近傍罫線へのスナップ確認"""
        anchors = [
            {
                "text": "テスト",
                "font_size": 10,
                "anchor": {"x_line": 10.0, "y_line": 50.0},  # 参照位置
                "offset": {"dx": 0.0, "dy": 0.0},
            },
        ]
        lines = [
            {"x0": 10.2, "y0": 0, "x1": 10.2, "y1": 200},  # 実際の罫線（微妙にずれ）
            {"x0": 0, "y0": 49.8, "x1": 100, "y1": 49.8},
        ]

        result = resolve_texts_from_anchors(anchors, lines, tol=0.5)

        # 最近傍の罫線（10.2, 49.8）にスナップされる
        assert abs(result[0]["x"] - 10.2) < 0.01
        assert abs(result[0]["y"] - 49.8) < 0.01
