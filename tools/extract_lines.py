import json
import re
from collections import defaultdict
from typing import Any

import fitz  # PyMuPDF


def _parse_dashes(dashes_str: str) -> tuple[list[float], float]:
    """
    PyMuPDFのdashes文字列をパースする

    Args:
        dashes_str: PyMuPDFのdashes文字列（例: "[] 0", "[3 3] 0"）

    Returns:
        (dash_pattern, dash_phase) のタプル
    """
    match = re.match(r"\[([\d\s.]*)\]\s*([\d.]+)", dashes_str.strip())
    if not match:
        return [], 0

    pattern_str, phase_str = match.groups()
    pattern = [float(x) for x in pattern_str.split()] if pattern_str.strip() else []
    phase = float(phase_str)
    return pattern, phase


def _cluster_positions(vals, tol=1.0):
    vals = sorted(vals)
    clusters = []
    for v in vals:
        if not clusters or abs(v - clusters[-1][-1]) > tol:
            clusters.append([v])
        else:
            clusters[-1].append(v)
    return clusters


def _merge_intervals(intervals, tol=1.2):
    """
    同一直線上で分割された線分を結合する

    Args:
        intervals: (start, end, width, dash_pattern, dash_phase, cap, join, color) のリスト
        tol: 結合の許容誤差（単位: pt）

    Returns:
        結合された線分のリスト
    """
    intervals = sorted(intervals, key=lambda t: (t[0], t[1]))
    merged = []
    for item in intervals:
        s, e, w, dash_pat, dash_ph, cap, join, color = item
        if not merged:
            merged.append([s, e, w, dash_pat, dash_ph, cap, join, color])
        else:
            ps, pe, pw, p_dash_pat, p_dash_ph, p_cap, p_join, p_color = merged[-1]
            # 線幅と描画属性が同じ場合のみ結合
            if (
                s <= pe + tol
                and abs(w - pw) < 0.01
                and dash_pat == p_dash_pat
                and dash_ph == p_dash_ph
                and cap == p_cap
                and join == p_join
                and color == p_color
            ):
                merged[-1][1] = max(pe, e)
            else:
                merged.append([s, e, w, dash_pat, dash_ph, cap, join, color])
    return [
        (s, e, w, dash_pat, dash_ph, cap, join, color)
        for s, e, w, dash_pat, dash_ph, cap, join, color in merged
    ]


def extract_lines_a3_to_a4x2(pdf_path: str) -> dict[str, Any]:
    """
    A3横のJIS規格PDFから罫線を抽出し、A4 x 2ページのレイアウトデータに変換する

    Args:
        pdf_path: 参照PDFのファイルパス

    Returns:
        レイアウトデータ（v2フォーマット、dict形式）
    """
    # 1) PDFを開いて罫線データを抽出
    with fitz.open(pdf_path) as doc:
        page = doc[0]
        W, H = page.rect.width, page.rect.height
        mid = W / 2

        # グラフィックス状態の継承を考慮（PDF仕様: 未指定時は前回値を継承）
        last_cap = 0  # PDF初期値: butt cap
        last_join = 0  # PDF初期値: mitre join

        segs = []
        for d in page.get_drawings():
            # 線幅の取得
            w = d.get("width", 1.0) or 1.0

            # 線種・端部・色の取得
            dashes_str = d.get("dashes")
            line_cap_tuple = d.get("lineCap")
            line_join_raw = d.get("lineJoin")
            color_tuple = d.get("color")

            # dashes: Noneの場合はデフォルトで実線
            if dashes_str is None:
                dashes_str = "[] 0"

            # lineCap: None時は前回値を継承（PDF仕様準拠）
            if line_cap_tuple is None:
                line_cap = last_cap
            elif isinstance(line_cap_tuple, tuple):
                line_cap = int(line_cap_tuple[0])
                last_cap = line_cap
            else:
                line_cap = int(line_cap_tuple)
                last_cap = line_cap

            # lineJoin: None時は前回値を継承（PDF仕様準拠）
            if line_join_raw is None:
                line_join = last_join
            else:
                line_join = int(line_join_raw)
                last_join = line_join

            # color: Noneの場合はデフォルトで黒
            if color_tuple is None:
                color = [0.0, 0.0, 0.0]
            else:
                color = list(color_tuple)

            # dashes: 文字列をパース
            dash_pattern, dash_phase = _parse_dashes(dashes_str)

            # 線分を抽出
            for it in d["items"]:
                op = it[0]
                if op == "l":  # line
                    p1, p2 = it[1], it[2]
                    segs.append(
                        (
                            p1.x,
                            p1.y,
                            p2.x,
                            p2.y,
                            w,
                            dash_pattern,
                            dash_phase,
                            line_cap,
                            line_join,
                            color,
                        )
                    )
                elif op == "re":  # rect -> 4 edges
                    r = it[1]
                    segs += [
                        (
                            r.x0,
                            r.y0,
                            r.x1,
                            r.y0,
                            w,
                            dash_pattern,
                            dash_phase,
                            line_cap,
                            line_join,
                            color,
                        ),
                        (
                            r.x1,
                            r.y0,
                            r.x1,
                            r.y1,
                            w,
                            dash_pattern,
                            dash_phase,
                            line_cap,
                            line_join,
                            color,
                        ),
                        (
                            r.x1,
                            r.y1,
                            r.x0,
                            r.y1,
                            w,
                            dash_pattern,
                            dash_phase,
                            line_cap,
                            line_join,
                            color,
                        ),
                        (
                            r.x0,
                            r.y1,
                            r.x0,
                            r.y0,
                            w,
                            dash_pattern,
                            dash_phase,
                            line_cap,
                            line_join,
                            color,
                        ),
                    ]

    # 2) 水平/垂直に分類（PyMuPDF座標：左上原点・y下向き）
    h = []  # (x0, y, x1, w, dash_pattern, dash_phase, cap, join, color)
    v = []  # (x, y0, y1, w, dash_pattern, dash_phase, cap, join, color)
    for x0, y0, x1, y1, w, dash_pat, dash_ph, cap, join, color in segs:
        if abs(y0 - y1) < 0.1 and abs(x0 - x1) > 0.5:
            h.append((min(x0, x1), y0, max(x0, x1), w, dash_pat, dash_ph, cap, join, color))
        elif abs(x0 - x1) < 0.1 and abs(y0 - y1) > 0.5:
            v.append((x0, min(y0, y1), max(y0, y1), w, dash_pat, dash_ph, cap, join, color))

    # 3) 左右に振り分け
    left_h = [s for s in h if s[2] <= mid + 0.5]
    right_h = [s for s in h if s[0] >= mid - 0.5]
    left_v = [s for s in v if s[0] <= mid + 0.5]
    right_v = [s for s in v if s[0] >= mid - 0.5]

    def to_reportlab(h_segs, v_segs, x_shift):
        """
        PyMuPDF座標系をReportLab座標系に変換し、v2フォーマット（dict形式）で出力

        Args:
            h_segs: 水平線のリスト
            v_segs: 垂直線のリスト
            x_shift: X座標のオフセット（右ページは mid）

        Returns:
            線分データのリスト（dict形式）
        """
        out = []

        # horizontal: group by y and attributes
        by_y_attr = defaultdict(list)
        for x0, y, x1, w, dash_pat, dash_ph, cap, join, color in h_segs:
            yk = round(y, 2)
            # 属性をキーに含める（タプルなのでハッシュ可能）
            attr_key = (yk, round(w, 3), tuple(dash_pat), dash_ph, cap, join, tuple(color))
            by_y_attr[attr_key].append((x0 - x_shift, x1 - x_shift))

        for (yk, w, dash_pat_tuple, dash_ph, cap, join, color_tuple), xs in by_y_attr.items():
            # 同じ属性の線分をマージ
            dash_pat = list(dash_pat_tuple)
            color = list(color_tuple)
            intervals = [
                (min(a, b), max(a, b), w, dash_pat, dash_ph, cap, join, color) for a, b in xs
            ]
            for s, e, w_merged, dash_pat, dash_ph, cap, join, color in _merge_intervals(
                intervals, tol=1.2
            ):
                y_rl = H - yk
                out.append(
                    {
                        "x0": s,
                        "y0": y_rl,
                        "x1": e,
                        "y1": y_rl,
                        "width": w_merged,
                        "dash_pattern": dash_pat,
                        "dash_phase": dash_ph,
                        "cap": cap,
                        "join": join,
                        "color": color,
                    }
                )

        # vertical: group by x and attributes
        by_x_attr = defaultdict(list)
        for x, y0, y1, w, dash_pat, dash_ph, cap, join, color in v_segs:
            xk = round(x, 2)
            attr_key = (xk, round(w, 3), tuple(dash_pat), dash_ph, cap, join, tuple(color))
            by_x_attr[attr_key].append((y0, y1))

        for (xk, w, dash_pat_tuple, dash_ph, cap, join, color_tuple), ys in by_x_attr.items():
            dash_pat = list(dash_pat_tuple)
            color = list(color_tuple)
            intervals = [
                (min(a, b), max(a, b), w, dash_pat, dash_ph, cap, join, color) for a, b in ys
            ]
            for s, e, w_merged, dash_pat, dash_ph, cap, join, color in _merge_intervals(
                intervals, tol=1.2
            ):
                x_rl = xk - x_shift
                y0_rl = H - e
                y1_rl = H - s
                out.append(
                    {
                        "x0": x_rl,
                        "y0": y0_rl,
                        "x1": x_rl,
                        "y1": y1_rl,
                        "width": w_merged,
                        "dash_pattern": dash_pat,
                        "dash_phase": dash_ph,
                        "cap": cap,
                        "join": join,
                        "color": color,
                    }
                )

        # 座標を丸める（0.001pt精度）
        for line in out:
            line["x0"] = round(line["x0"], 3)
            line["y0"] = round(line["y0"], 3)
            line["x1"] = round(line["x1"], 3)
            line["y1"] = round(line["y1"], 3)
            line["width"] = round(line["width"], 3)

        # 読みやすくソート
        out.sort(key=lambda r: (r["y0"], r["x0"], r["y1"], r["x1"]))
        return out

    page1 = to_reportlab(left_h, left_v, x_shift=0.0)
    page2 = to_reportlab(right_h, right_v, x_shift=mid)

    return {
        "source_page_size_pt": [round(W, 2), round(H, 2)],
        "split_x_pt": round(mid, 2),
        "page1_lines": page1,  # A4(左) 用の線分（dict形式）
        "page2_lines": page2,  # A4(右) 用の線分（dict形式）
    }


if __name__ == "__main__":
    from pathlib import Path

    pdf_path = Path(__file__).parent.parent / "tests/fixtures/R3_pdf_rirekisyo.pdf"
    output_path = Path(__file__).parent.parent / "skill/assets/data/a4/rirekisho_layout.json"

    data = extract_lines_a3_to_a4x2(str(pdf_path))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✓ Layout data extracted (v2 format)")
    print(f"  page1: {len(data['page1_lines'])} segments")
    print(f"  page2: {len(data['page2_lines'])} segments")
    print(f"  Output: {output_path}")
