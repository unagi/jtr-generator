import json
from collections import defaultdict
import fitz  # PyMuPDF

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
    # intervals: (start, end, width)
    intervals = sorted(intervals, key=lambda t: (t[0], t[1]))
    merged = []
    for s, e, w in intervals:
        if not merged:
            merged.append([s, e, w])
        else:
            ps, pe, pw = merged[-1]
            if s <= pe + tol and abs(w - pw) < 0.01:
                merged[-1][1] = max(pe, e)
            else:
                merged.append([s, e, w])
    return [(s, e, w) for s, e, w in merged]

def extract_lines_a3_to_a4x2(pdf_path: str):
    doc = fitz.open(pdf_path)
    page = doc[0]
    W, H = page.rect.width, page.rect.height
    mid = W / 2

    # 1) drawing commandsから線分を集める（line + rect edges）
    segs = []
    for d in page.get_drawings():
        w = d.get("width", 1.0) or 1.0
        for it in d["items"]:
            op = it[0]
            if op == "l":  # line
                p1, p2 = it[1], it[2]
                segs.append((p1.x, p1.y, p2.x, p2.y, w))
            elif op == "re":  # rect -> 4 edges
                r = it[1]
                segs += [
                    (r.x0, r.y0, r.x1, r.y0, w),
                    (r.x1, r.y0, r.x1, r.y1, w),
                    (r.x1, r.y1, r.x0, r.y1, w),
                    (r.x0, r.y1, r.x0, r.y0, w),
                ]

    # 2) 水平/垂直に分類（PyMuPDF座標：左上原点・y下向き）
    h = []  # (x0, y, x1, w)
    v = []  # (x, y0, y1, w)
    for x0, y0, x1, y1, w in segs:
        if abs(y0 - y1) < 0.1 and abs(x0 - x1) > 0.5:
            h.append((min(x0, x1), y0, max(x0, x1), w))
        elif abs(x0 - x1) < 0.1 and abs(y0 - y1) > 0.5:
            v.append((x0, min(y0, y1), max(y0, y1), w))

    # 3) 左右に振り分け
    left_h = [s for s in h if s[2] <= mid + 0.5]
    right_h = [s for s in h if s[0] >= mid - 0.5]
    left_v = [s for s in v if s[0] <= mid + 0.5]
    right_v = [s for s in v if s[0] >= mid - 0.5]

    def to_reportlab(h_segs, v_segs, x_shift):
        # PyMuPDF -> ReportLab（左下原点・y上向き）
        # さらに右ページは x を -mid して A4座標へ
        # まず “同一直線上で分割されている線” をマージ
        out = []

        # horizontal: group by y
        by_y = defaultdict(list)
        for x0, y, x1, w in h_segs:
            yk = round(y, 2)
            by_y[yk].append((x0 - x_shift, x1 - x_shift, w))

        for yk, xs in by_y.items():
            # width別にinterval merge
            by_w = defaultdict(list)
            for a, b, w in xs:
                by_w[round(w, 2)].append((min(a, b), max(a, b), w))
            for _, intervals in by_w.items():
                for s, e, w in _merge_intervals(intervals, tol=1.2):
                    y_rl = H - yk
                    out.append([s, y_rl, e, y_rl, float(w)])

        # vertical: group by x
        by_x = defaultdict(list)
        for x, y0, y1, w in v_segs:
            xk = round(x, 2)
            by_x[xk].append((y0, y1, w))

        for xk, ys in by_x.items():
            by_w = defaultdict(list)
            for a, b, w in ys:
                by_w[round(w, 2)].append((min(a, b), max(a, b), w))
            for _, intervals in by_w.items():
                for s, e, w in _merge_intervals(intervals, tol=1.2):
                    x_rl = xk - x_shift
                    y0_rl = H - e
                    y1_rl = H - s
                    out.append([x_rl, y0_rl, x_rl, y1_rl, float(w)])

        # 読みやすくソート＆丸め
        out = [[round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2), round(w, 3)]
               for x0, y0, x1, y1, w in out]
        out.sort(key=lambda r: (r[1], r[0], r[3], r[2]))
        return out

    page1 = to_reportlab(left_h, left_v, x_shift=0.0)
    page2 = to_reportlab(right_h, right_v, x_shift=mid)

    return {
        "source_page_size_pt": [round(W, 2), round(H, 2)],
        "split_x_pt": round(mid, 2),
        "page1_lines": page1,  # A4(左) 用の線分
        "page2_lines": page2,  # A4(右) 用の線分
    }

if __name__ == "__main__":
    from pathlib import Path

    pdf_path = Path(__file__).parent.parent / "tests/fixtures/R3_pdf_rirekisyo.pdf"
    output_path = Path(__file__).parent.parent / "data/layouts/resume_layout_a4.json"

    data = extract_lines_a3_to_a4x2(str(pdf_path))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Layout data extracted")
    print(f"  page1: {len(data['page1_lines'])} segments")
    print(f"  page2: {len(data['page2_lines'])} segments")
    print(f"  Output: {output_path}")
