"""Auto-label paired captures: one classical mask per (lensId, pos), copied to every photo of the group.

Photos are named <lensId>_<pos>_<cond>.jpg, cond == "easy" being the backlit shot taken first.
Every photo is rectified to the lens window (PX_PER_MM = 10, so 800x650 px for an 80x65 mm window)
with the ArUco markers of board_spec.json. The easy shot gives the mask (flat-field, black-hat,
Otsu, fill from the border, largest component). The mask is valid for the other photos only if
the stand did not move: otherwise the group is rejected.

Usage:  python autolabel.py PHOTOS_DIR --spec board_spec.json [--out DIR] [--qc N]
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from pathlib import Path

import cv2
import numpy as np

PX_PER_MM = 10
MAX_SHIFT_PX = 3.0            # window-corner drift (photo pixels) tolerated against the easy shot
MIN_AREA_MM2, MAX_AREA_MM2 = 600.0, 4500.0   # plausible lens area (strat3 section 4.2: 600..4000, slightly relaxed)
NAME_RE = re.compile(r"^(?P<lens>.+)_(?P<pos>[^_]+)_(?P<cond>[^_]+)\.(jpg|jpeg|png)$", re.IGNORECASE)
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "_local" / "real"


def imread(path: Path) -> np.ndarray | None:
    """cv2.imread fails on non-ASCII Windows paths; imdecode applies the EXIF orientation like imread."""
    buf = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR) if buf.size else None


def imwrite(path: Path, img: np.ndarray, quality: int = 95) -> None:
    ext = path.suffix.lower()
    params = [cv2.IMWRITE_JPEG_QUALITY, quality] if ext in (".jpg", ".jpeg") else []
    ok, buf = cv2.imencode(ext, img, params)
    if not ok:
        raise OSError(f"cannot encode {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    buf.tofile(str(path))


def window_size_px(spec: dict) -> tuple[int, int]:
    return round(spec["windowMm"]["w"] * PX_PER_MM), round(spec["windowMm"]["h"] * PX_PER_MM)


def board_homography(img: np.ndarray, spec: dict, min_markers: int = 3) -> np.ndarray | None:
    """3x3 matrix mapping photo pixels to window pixels (board mm * PX_PER_MM), or None if too few markers."""
    name = spec.get("dictionary", "DICT_4X4_50")
    dico = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, name if name.startswith("DICT_") else "DICT_" + name))
    corners, ids, _ = cv2.aruco.ArucoDetector(dico, cv2.aruco.DetectorParameters()).detectMarkers(img)
    if ids is None:
        return None
    wanted = {m["id"]: np.asarray(m["corners"], np.float32) * PX_PER_MM for m in spec["markers"]}
    src, dst = [], []
    n_found = 0
    for c, i in zip(corners, ids.ravel()):
        if int(i) in wanted:
            src.append(c.reshape(4, 2))
            dst.append(wanted[int(i)])
            n_found += 1
    if n_found < min(min_markers, len(wanted)):
        return None
    H, _ = cv2.findHomography(np.concatenate(src), np.concatenate(dst), cv2.RANSAC, 3.0)
    return H


def window_corners_in_photo(H: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    w, h = size
    quad = np.array([[[0, 0], [w, 0], [w, h], [0, h]]], np.float32)
    return cv2.perspectiveTransform(quad, np.linalg.inv(H))[0]


def rectify(img: np.ndarray, H: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    return cv2.warpPerspective(img, H, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def classic_mask(rect: np.ndarray) -> np.ndarray | None:
    """Classical lens mask of a rectified backlit shot: uint8 0/255, or None if implausible."""
    gray = cv2.cvtColor(rect, cv2.COLOR_BGR2GRAY).astype(np.float32)
    flat = gray / (cv2.GaussianBlur(gray, (0, 0), 10 * PX_PER_MM) + 1.0)           # flat-field
    flat = np.clip(flat / 1.5, 0, 1) * 255
    flat = cv2.GaussianBlur(flat.astype(np.uint8), (0, 0), 0.7)
    # kernel wider than the widest rim (1.5 mm) so the whole band is picked up
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2.5 * PX_PER_MM) | 1,) * 2)
    bh = cv2.morphologyEx(flat, cv2.MORPH_BLACKHAT, ker)
    _, th = cv2.threshold(bh, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # drop components touching the window border (markers' shadows, window frame)
    n, lab, st, _ = cv2.connectedComponentsWithStats(th, connectivity=8)
    h, w = th.shape
    for i in range(1, n):
        x, y, cw, ch, _a = st[i]
        if x == 0 or y == 0 or x + cw == w or y + ch == h:
            th[lab == i] = 0
    close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (PX_PER_MM | 1,) * 2)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, close)
    pad = cv2.copyMakeBorder(th, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    cv2.floodFill(pad, None, (0, 0), 128)                                          # background reachable from the border
    filled = np.where(pad[1:-1, 1:-1] == 128, 0, 255).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(filled, connectivity=8)
    if n < 2:
        return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    mask = np.where(lab == k, 255, 0).astype(np.uint8)
    area_mm2 = st[k, cv2.CC_STAT_AREA] / PX_PER_MM**2
    return mask if MIN_AREA_MM2 <= area_mm2 <= MAX_AREA_MM2 else None


def overlay(rect: np.ndarray, mask: np.ndarray, label: str) -> np.ndarray:
    out = rect.copy()
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(out, cnts, -1, (0, 0, 255), 1, cv2.LINE_AA)
    cv2.putText(out, label, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1, cv2.LINE_AA)
    return out


def group_photos(folder: Path) -> tuple[dict[tuple[str, str], list[tuple[str, Path]]], list[Path]]:
    groups: dict[tuple[str, str], list[tuple[str, Path]]] = {}
    skipped = []
    for p in sorted(folder.iterdir()):
        m = NAME_RE.match(p.name) if p.is_file() else None
        if m:
            groups.setdefault((m["lens"], m["pos"]), []).append((m["cond"], p))
        elif p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            skipped.append(p)
    return groups, skipped


def run(photos: Path, spec: dict, out: Path, qc: int = 0, seed: int = 0, max_shift: float = MAX_SHIFT_PX) -> dict:
    size = window_size_px(spec)
    groups, skipped = group_photos(photos)
    rejected: list[tuple[str, str, str]] = [(p.name, "", "name does not match <lensId>_<pos>_<cond>") for p in skipped]
    groups_rejected = 0
    accepted: list[tuple[str, str, str, str, np.ndarray, np.ndarray]] = []   # file, lens, pos, cond, rect, mask

    for (lens, pos), items in groups.items():
        gname = f"{lens}_{pos}"
        easy = [p for c, p in items if c.lower() == "easy"]
        if not easy:
            rejected.append((gname, "", "no easy shot"))
            groups_rejected += 1
            continue
        img_e = imread(easy[0])
        H_e = board_homography(img_e, spec) if img_e is not None else None
        if H_e is None:
            rejected.append((gname, easy[0].name, "markers not found in easy shot"))
            groups_rejected += 1
            continue
        rect_e = rectify(img_e, H_e, size)
        mask = classic_mask(rect_e)
        if mask is None:
            rejected.append((gname, easy[0].name, "no plausible lens mask in easy shot"))
            groups_rejected += 1
            continue
        corners_e = window_corners_in_photo(H_e, size)
        rows, reason = [], ""
        for cond, p in items:
            if p == easy[0]:
                rows.append((p.name, cond, rect_e))
                continue
            img = imread(p)
            H = board_homography(img, spec) if img is not None else None
            if H is None:       # cannot be rectified or checked: drop this photo only
                rejected.append((gname, p.name, "markers not found, photo dropped"))
                continue
            drift = float(np.linalg.norm(window_corners_in_photo(H, size) - corners_e, axis=1).max())
            if img.shape != img_e.shape or drift > max_shift:
                reason = f"{p.name}: window corners {drift:.1f} px from easy shot (stand moved)"
                break
            rows.append((p.name, cond, rectify(img, H, size)))
        if reason:
            rejected.append((gname, "", reason))
            groups_rejected += 1
            continue
        for name, cond, rect in rows:
            accepted.append((name, lens, pos, cond, rect, mask))

    for sub in ("images", "masks"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    with open(out / "index.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["file", "lensId", "pos", "cond", "source"])
        for name, lens, pos, cond, rect, mask in accepted:
            stem = f"{lens}_{pos}_{cond}"
            imwrite(out / "images" / (stem + ".jpg"), rect)
            imwrite(out / "masks" / (stem + ".png"), mask)
            wr.writerow([stem + ".jpg", lens, pos, cond, "real"])
    with open(out / "rejected.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["group_or_file", "file", "reason"])
        wr.writerows(rejected)

    n_qc = 0
    if qc > 0:
        hard = [a for a in accepted if a[3].lower() != "easy"] or accepted
        for name, lens, pos, cond, rect, mask in random.Random(seed).sample(hard, min(qc, len(hard))):
            imwrite(out / "qc" / f"{lens}_{pos}_{cond}.jpg", overlay(rect, mask, f"{lens}_{pos}_{cond}"))
            n_qc += 1
    return {"accepted": len(accepted), "groups_rejected": groups_rejected,
            "rejected": rejected, "qc": n_qc}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photos", type=Path, help="folder of <lensId>_<pos>_<cond>.jpg")
    ap.add_argument("--spec", type=Path, required=True, help="board_spec.json")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default training/_local/real)")
    ap.add_argument("--qc", type=int, default=0, help="write N overlay images (mask outline on a hard shot) into OUT/qc/")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-shift", type=float, default=MAX_SHIFT_PX, help="px of window-corner drift tolerated")
    a = ap.parse_args(argv)
    import json
    res = run(a.photos, json.loads(a.spec.read_text(encoding="utf-8")), a.out, a.qc, a.seed, a.max_shift)
    print(f"{res['accepted']} photos labelled, {len(res['rejected'])} rejections (see {a.out / 'rejected.csv'}), {res['qc']} qc overlays")
    return 0


if __name__ == "__main__":
    sys.exit(main())
