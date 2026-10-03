"""Low-level PDF parsing helpers for strategy 1 (ground truth from the specimen PDF).

Everything here works on the vector/text layer of
`data/Paper Registry/dossiers_specimen_10_patientes.pdf` (PyMuPDF).

Key facts (verified, see work/strat1/REPORT.md):
  * 80 pages = 10 patients x 8 page types, page index n -> patient n//8+1, page_type n%8+1.
  * Printed form text is Helvetica / Helvetica-Bold; every filled-in value is one of five
    handwriting fonts (Caveat, NanumPen, Gaegu, ShadowsIntoLight, ReenieBeanie), one glyph per span.
  * Every page is the same template rigidly rotated by -0.8..+0.8 degrees and shifted by up to
    ~6 pt.  A similarity transform fitted on matching printed words recovers it exactly (residual 0),
    so zone templates are expressed in the frame of patient 1's page of the same type
    (the "reference frame") and every other page is aligned onto it.
  * Checkbox = 4 line items forming an ~8x8 pt square (dark ink); a tick is 2 separate blue
    1-line drawings (an X) centred on the square.  Underline of a fill-in field = 1 long line, 0.4 wide.
  * Pixel scale PDF->PNG: 200/72.
"""
from __future__ import annotations

import collections
import math
import re
from pathlib import Path

import numpy as np
import pymupdf

ROOT = Path(__file__).resolve().parents[2]            # dayone-participants/
PDF_PATH = ROOT / "data" / "Paper Registry" / "dossiers_specimen_10_patientes.pdf"
PNG_DIR = ROOT / "data" / "Paper Registry"
SCALE = 200.0 / 72.0

HAND_FONTS = ("Caveat", "NanumPen", "Gaegu", "ShadowsIntoLight", "ReenieBeanie")


def is_hand(font: str) -> bool:
    return not font.startswith("Helvetica")


def open_pdf() -> pymupdf.Document:
    return pymupdf.open(str(PDF_PATH))


def page_to_patient_type(n: int) -> tuple[int, int]:
    """0-based PDF page index -> (patient 1..10, page_type 1..8)."""
    return n // 8 + 1, n % 8 + 1


# ----------------------------------------------------------------------------------------------
# characters
# ----------------------------------------------------------------------------------------------
class Ch:
    __slots__ = ("x0", "y0", "x1", "y1", "c", "font", "size")

    def __init__(self, bbox, c, font, size):
        self.x0, self.y0, self.x1, self.y1 = bbox
        self.c, self.font, self.size = c, font, size

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2

    @property
    def hand(self):
        return is_hand(self.font)


def page_chars(page) -> list[Ch]:
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                for c in s["chars"]:
                    out.append(Ch(c["bbox"], c["c"], s["font"], s["size"]))
    return out


def cluster_chars(chars: list[Ch], max_gap=2.5, max_dy=5.0) -> list[list[Ch]]:
    """Union-find clustering of characters into words/phrases (same line, small x gap)."""
    n = len(chars)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(range(n), key=lambda i: chars[i].x0)
    for ii, i in enumerate(order):
        a = chars[i]
        for j in order[ii + 1:]:
            b = chars[j]
            if b.x0 - a.x1 > max_gap + 12:      # sorted by x0: cannot link any further
                break
            gap = max(a.x0, b.x0) - min(a.x1, b.x1)
            if abs(a.cy - b.cy) < max_dy and gap < max_gap:
                parent[find(i)] = find(j)
    groups = collections.defaultdict(list)
    for i in range(n):
        groups[find(i)].append(chars[i])
    res = []
    for g in groups.values():
        g.sort(key=lambda c: c.x0)
        res.append(g)
    res.sort(key=lambda g: (round(sum(c.cy for c in g) / len(g) / 4), g[0].x0))
    return res


def chars_text(chars: list[Ch], line_tol=4.0) -> str:
    """Reading-order text of a set of characters (lines top->bottom, chars left->right)."""
    if not chars:
        return ""
    cs = sorted(chars, key=lambda c: c.cy)
    lines, cur = [], [cs[0]]
    for c in cs[1:]:
        if abs(c.cy - cur[-1].cy) <= line_tol:
            cur.append(c)
        else:
            lines.append(cur)
            cur = [c]
    lines.append(cur)
    out = []
    for ln in lines:
        ln.sort(key=lambda c: c.x0)
        out.append("".join(c.c for c in ln))
    txt = " ".join(out)
    return re.sub(r"\s+", " ", txt).strip()


def printed_words(page) -> list[tuple[str, float, float, tuple]]:
    """Printed (Helvetica) words: (text, cx, cy, bbox)."""
    cs = [c for c in page_chars(page) if not c.hand and c.c.strip()]
    res = []
    for g in cluster_chars(cs, max_gap=1.3, max_dy=2.5):
        t = "".join(c.c for c in g)
        x0 = min(c.x0 for c in g); y0 = min(c.y0 for c in g)
        x1 = max(c.x1 for c in g); y1 = max(c.y1 for c in g)
        res.append((t, (x0 + x1) / 2, (y0 + y1) / 2, (x0, y0, x1, y1)))
    return res


# ----------------------------------------------------------------------------------------------
# alignment onto the reference frame (patient 1's page of the same type)
# ----------------------------------------------------------------------------------------------
class Align:
    """Similarity transform z' = a*z + b (complex plane), page frame -> reference frame."""

    def __init__(self, a=1 + 0j, b=0j, n_match=0, resid=0.0):
        self.a, self.b, self.n_match, self.resid = a, b, n_match, resid

    def fwd(self, x, y):
        z = self.a * complex(x, y) + self.b
        return z.real, z.imag

    def inv(self, x, y):
        z = (complex(x, y) - self.b) / self.a
        return z.real, z.imag

    @property
    def rot_deg(self):
        return math.degrees(np.angle(self.a))


def _fit(src, dst):
    z = np.array([complex(*s) for s in src]); w = np.array([complex(*d) for d in dst])
    zm, wm = z.mean(), w.mean()
    a = np.sum(np.conj(z - zm) * (w - wm)) / np.sum(np.abs(z - zm) ** 2)
    return a, wm - a * zm


def compute_align(page, ref_words) -> Align:
    """Fit page -> reference frame using printed words that are unique in both pages."""
    cur = printed_words(page)
    refc = collections.Counter(t for t, *_ in ref_words)
    curc = collections.Counter(t for t, *_ in cur)
    rd = {t: (x, y) for t, x, y, _ in ref_words}
    cd = {t: (x, y) for t, x, y, _ in cur}
    common = [t for t in refc if refc[t] == 1 and curc.get(t) == 1 and len(t) >= 2]
    if len(common) < 4:
        return Align(n_match=len(common), resid=float("nan"))
    src = [cd[t] for t in common]; dst = [rd[t] for t in common]
    keep = list(range(len(common)))
    for _ in range(4):                       # robust: drop outliers (words that moved, e.g. name)
        a, b = _fit([src[i] for i in keep], [dst[i] for i in keep])
        res = np.array([abs(a * complex(*src[i]) + b - complex(*dst[i])) for i in range(len(common))])
        thr = max(1.5, 3 * np.median(res[keep]))
        new = [i for i in range(len(common)) if res[i] <= thr]
        if len(new) == len(keep) or len(new) < 4:
            break
        keep = new
    a, b = _fit([src[i] for i in keep], [dst[i] for i in keep])
    res = [abs(a * complex(*src[i]) + b - complex(*dst[i])) for i in keep]
    return Align(a, b, len(keep), float(np.max(res)))


# ----------------------------------------------------------------------------------------------
# vector graphics
# ----------------------------------------------------------------------------------------------
def _segments(dr):
    segs = []
    for it in dr["items"]:
        if it[0] == "l":
            segs.append((it[1].x, it[1].y, it[2].x, it[2].y))
    return segs


def is_blue(color) -> bool:
    return bool(color) and len(color) == 3 and color[2] > 0.4 and color[0] < 0.25 and color[1] < 0.3


def squares(page) -> list[dict]:
    """Checkbox squares: drawings made of 4 line items with an ~8x8 pt bounding box."""
    out = []
    for dr in page.get_drawings():
        segs = _segments(dr)
        if len(segs) == 4 and dr["type"] == "s" and not is_blue(dr["color"]):
            r = dr["rect"]
            if 6.5 <= r.width <= 10.5 and 6.5 <= r.height <= 10.5:
                xs = [s[0] for s in segs] + [s[2] for s in segs]
                ys = [s[1] for s in segs] + [s[3] for s in segs]
                out.append({"cx": sum(xs) / 8 * 1.0 if False else (min(xs) + max(xs)) / 2,
                            "cy": (min(ys) + max(ys)) / 2, "w": r.width, "h": r.height})
    return out


def tick_segments(page) -> list[dict]:
    """Blue single-line drawings (the two strokes of a hand-drawn X)."""
    out = []
    for dr in page.get_drawings():
        if dr["type"] == "s" and is_blue(dr["color"]):
            for s in _segments(dr):
                out.append({"x0": s[0], "y0": s[1], "x1": s[2], "y1": s[3],
                            "cx": (s[0] + s[2]) / 2, "cy": (s[1] + s[3]) / 2})
    return out


def underlines(page, min_len=25.0) -> list[dict]:
    """Long thin single-line drawings in dark ink (fill-in underlines and table rules)."""
    out = []
    for dr in page.get_drawings():
        if dr["type"] != "s" or is_blue(dr["color"]):
            continue
        for s in _segments(dr):
            L = math.hypot(s[2] - s[0], s[3] - s[1])
            if L >= min_len:
                out.append({"x0": min(s[0], s[2]), "x1": max(s[0], s[2]),
                            "y0": s[1] if s[0] <= s[2] else s[3], "y1": s[3] if s[0] <= s[2] else s[1],
                            "w": dr["width"], "n_items": len(dr["items"]), "L": L})
    return out


def ticked_squares(page, sq=None, ticks=None) -> list[bool]:
    """For each square (same order as `squares`), True when >=2 tick strokes cross inside it."""
    sq = sq if sq is not None else squares(page)
    ticks = ticks if ticks is not None else tick_segments(page)
    res = []
    for s in sq:
        n = 0
        for t in ticks:
            if abs(t["cx"] - s["cx"]) <= 5.5 and abs(t["cy"] - s["cy"]) <= 5.5:
                n += 1
        res.append(n >= 2)
    return res
