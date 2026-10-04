import type { Pt } from '../contracts';

/**
 * Extent of the contour between two parallel lines at angle theta (radians) to the board x axis:
 * what a calliper reads. A = extentAlong(c, 0), B = extentAlong(c, PI / 2) (boxing system, strat8 4.2).
 */
export function extentAlong(contour: Pt[], theta: number): number {
  const ux = Math.cos(theta);
  const uy = Math.sin(theta);
  let lo = Infinity;
  let hi = -Infinity;
  for (const [x, y] of contour) {
    const p = x * ux + y * uy;
    if (p < lo) lo = p;
    if (p > hi) hi = p;
  }
  return hi - lo;
}

export function polygonLength(c: Pt[]): number {
  let s = 0;
  for (let i = 0; i < c.length; i++) {
    const a = c[i];
    const b = c[(i + 1) % c.length];
    s += Math.hypot(b[0] - a[0], b[1] - a[1]);
  }
  return s;
}

/** Shoelace area in the numeric (x, y) frame: positive = counter-clockwise order. */
export function signedArea(c: Pt[]): number {
  let s = 0;
  for (let i = 0; i < c.length; i++) {
    const a = c[i];
    const b = c[(i + 1) % c.length];
    s += a[0] * b[1] - b[0] * a[1];
  }
  return s / 2;
}

export interface Boxing { A: number; B: number; boxCentre: Pt; perimeter: number }

export function boxing(c: Pt[]): Boxing {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const [x, y] of c) {
    if (x < x0) x0 = x;
    if (x > x1) x1 = x;
    if (y < y0) y0 = y;
    if (y > y1) y1 = y;
  }
  return { A: extentAlong(c, 0), B: extentAlong(c, Math.PI / 2), boxCentre: [(x0 + x1) / 2, (y0 + y1) / 2], perimeter: polygonLength(c) };
}

function convexHull(points: Pt[]): Pt[] {
  const p = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o: Pt, a: Pt, b: Pt) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const build = (seq: Pt[]) => {
    const h: Pt[] = [];
    for (const q of seq) {
      while (h.length >= 2 && cross(h[h.length - 2], h[h.length - 1], q) <= 0) h.pop();
      h.push(q);
    }
    h.pop();
    return h;
  };
  return [...build(p), ...build([...p].reverse())];
}

export interface MinAreaRect { longAngleDeg: number; long: number; short: number }

/** Minimum-area bounding rectangle (rotating calipers over the hull edges). longAngleDeg is in (-90, 90]. */
export function minAreaRect(c: Pt[]): MinAreaRect {
  const hull = convexHull(c);
  let best: MinAreaRect | null = null;
  let bestArea = Infinity;
  for (let i = 0; i < hull.length; i++) {
    const a = hull[i];
    const b = hull[(i + 1) % hull.length];
    const th = Math.atan2(b[1] - a[1], b[0] - a[0]);
    const w = extentAlong(hull, th);
    const h = extentAlong(hull, th + Math.PI / 2);
    if (w * h < bestArea) {
      bestArea = w * h;
      let deg = ((w >= h ? th : th + Math.PI / 2) * 180) / Math.PI;
      deg = ((((deg + 90) % 180) + 180) % 180) - 90; // fold to [-90, 90)
      if (deg === -90) deg = 90;
      best = { longAngleDeg: deg, long: Math.max(w, h), short: Math.min(w, h) };
    }
  }
  return best ?? { longAngleDeg: 0, long: 0, short: 0 };
}
