"""Spatial reasoning on a drawing page: which callout belongs to which label.

Drawings state ownership by position, in three ways this module handles:

* a schedule with the labels in a header row  -> the callout is under its label;
* a schedule with the labels in a first column -> the callout is on its label's row;
* a detail or a plan view                      -> the callout is next to its label.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from ..models import BBox, Bar


def center(b: BBox) -> tuple[float, float]:
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)


def union(boxes: list[BBox]) -> BBox:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


@dataclass
class Label:
    label: str  # normalised (C12)
    text: str  # as written (C-12)
    bbox: BBox
    group: int = -1  # labels listed together ("B-12, B-13") share a group and their callouts

    @property
    def cx(self) -> float:
        return (self.bbox[0] + self.bbox[2]) / 2.0

    @property
    def cy(self) -> float:
        return (self.bbox[1] + self.bbox[3]) / 2.0


@dataclass
class Band:
    """Labels aligned on a row (axis='row') or stacked in a column (axis='col')."""

    axis: str
    pos: float  # y of a row band, x of a column band
    labels: list[Label] = field(default_factory=list)
    pitch: float = 0.0
    lo: float = 0.0
    hi: float = 0.0


def find_bands(labels: list[Label], min_labels: int = 3) -> list[Band]:
    bands: list[Band] = []
    if len(labels) < min_labels:
        return bands
    heights = [l.bbox[3] - l.bbox[1] for l in labels]
    tol_row = max(3.0, 0.7 * statistics.median(heights))
    for axis, tol in (("row", tol_row), ("col", 12.0)):
        key = (lambda l: l.cy) if axis == "row" else (lambda l: l.cx)
        along = (lambda l: l.cx) if axis == "row" else (lambda l: l.cy)
        ordered = sorted(labels, key=key)
        group: list[Label] = [ordered[0]]
        for lab in ordered[1:] + [None]:  # type: ignore[list-item]
            if lab is not None and abs(key(lab) - key(group[-1])) <= tol:
                group.append(lab)
                continue
            if len(group) >= min_labels and len({g.label for g in group}) >= min_labels:
                pts = sorted(along(g) for g in group)
                gaps = [b - a for a, b in zip(pts, pts[1:]) if b - a > 1.0]
                if gaps:
                    bands.append(
                        Band(axis=axis, pos=statistics.fmean(key(g) for g in group), labels=list(group),
                             pitch=statistics.median(gaps), lo=pts[0], hi=pts[-1])
                    )
            if lab is not None:
                group = [lab]
    return bands


def assign_labels(bars: list[Bar], labels: list[Label], radius: float, header_pull: float = 0.35) -> list[Label | None]:
    """For each callout, the label that owns it (or None).

    `header_pull` is how fast a row or column of labels loses its hold with
    distance: low (0.1) reads the page as a schedule whose headers own
    everything below them, high (0.35) as rows of details each titled nearby.
    """
    bands = find_bands(labels)
    out: list[Label | None] = []
    for bar in bars:
        cx, cy = center(bar.bbox)
        best: tuple[float, Label] | None = None

        for band in bands:
            reach = 0.6 * band.pitch
            if band.axis == "row":
                if band.pos >= cy - 1.0 or not (band.lo - reach <= cx <= band.hi + reach):
                    continue
                lab = min(band.labels, key=lambda l: abs(l.cx - cx))
                off, away = abs(lab.cx - cx), cy - band.pos
            else:
                if band.pos >= cx - 1.0 or not (band.lo - reach <= cy <= band.hi + reach):
                    continue
                lab = min(band.labels, key=lambda l: abs(l.cy - cy))
                off, away = abs(lab.cy - cy), cx - band.pos
            if off <= reach:
                # A header owns what is under it, but less and less with distance, so that the title
                # of a detail (close by) is not overruled by the titles of the row of details above.
                cost = off + min(header_pull * away, 1.2 * radius)
                if best is None or cost < best[0]:
                    best = (cost, lab)

        # Details, sections and elevations: the title sits under its view and the
        # view is wider than tall, so a label below and to the side is favoured
        # over one above.
        for lab in labels:
            dx, dy = abs(lab.cx - cx), lab.cy - cy
            d = ((0.6 * dx) ** 2 + (dy if dy >= 0 else 2.5 * dy) ** 2) ** 0.5
            if d <= radius:
                cost = d if d < 90.0 else 1.3 * d
                if best is None or cost < best[0]:
                    best = (cost, lab)

        out.append(best[1] if best and best[0] <= 1.5 * radius else None)
    return out


def cluster_stacked(bars: list[Bar], gap: float) -> list[list[Bar]]:
    """Group callouts written as one multi-line annotation (stacked, overlapping in x)."""
    n = len(bars)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(range(n), key=lambda i: bars[i].bbox[1])
    for a_pos, i in enumerate(order):
        bi = bars[i].bbox
        hi = max(bi[3] - bi[1], 1.0)
        for j in order[a_pos + 1:]:
            bj = bars[j].bbox
            if bj[1] - bi[3] > gap * hi:
                break
            overlap = min(bi[2], bj[2]) - max(bi[0], bj[0])
            if overlap > 0 and bj[1] - bi[3] <= gap * hi and abs((bj[3] - bj[1]) - hi) < 0.6 * hi:
                parent[find(i)] = find(j)
    groups: dict[int, list[Bar]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(bars[i])
    return list(groups.values())


def flag_bar_list_rows(bars: list[Bar], space_qty: list[bool], min_rows: int = 6, tol: float = 12.0) -> None:
    """Mark bar-list (bordereau) rows: `24 15M ...` entries stacked in a column."""
    idx = sorted((i for i, s in enumerate(space_qty) if s), key=lambda i: center(bars[i].bbox)[0])
    start = 0
    while start < len(idx):
        end = start
        while end + 1 < len(idx) and center(bars[idx[end + 1]].bbox)[0] - center(bars[idx[end]].bbox)[0] <= tol:
            end += 1
        if end - start + 1 >= min_rows:
            for k in idx[start: end + 1]:
                bars[k].bordereau = True
        start = end + 1


def assign_row_levels(bars: list[Bar], tokens: list[tuple[str, float, float]]) -> None:
    """Tag callouts sitting in a schedule row with that row's level.

    `tokens` are (level, cx, cy) of level names on the page.  Only level names
    stacked in a column (a schedule's row headers) are trusted.
    """
    if len(tokens) < 3:
        return
    ordered = sorted(tokens, key=lambda t: t[1])
    columns: list[list[tuple[str, float, float]]] = [[ordered[0]]]
    for tok in ordered[1:]:
        if tok[1] - columns[-1][-1][1] <= 40.0:
            columns[-1].append(tok)
        else:
            columns.append([tok])
    columns = [c for c in columns if len({t[0] for t in c}) >= 3]
    if not columns:
        return
    for bar in bars:
        cx, cy = center(bar.bbox)
        best: tuple[float, str] | None = None
        for col in columns:
            ys = sorted(t[2] for t in col)
            gaps = [b - a for a, b in zip(ys, ys[1:]) if b - a > 2.0]
            if not gaps:
                continue
            pitch = statistics.median(gaps)
            if not (ys[0] - pitch <= cy <= ys[-1] + pitch):
                continue
            near = min(col, key=lambda t: abs(t[2] - cy))
            off = abs(near[2] - cy)
            if off > 0.3 * pitch:
                # Between two level lines: the segment starts at the level drawn below it.
                below = [t for t in col if 0 < t[2] - cy <= pitch]
                if below:
                    near = min(below, key=lambda t: t[2] - cy)
                    off = near[2] - cy
            if off <= pitch and (best is None or abs(near[1] - cx) < best[0]):
                best = (abs(near[1] - cx), near[0])
        if best:
            bar.level = best[1]
