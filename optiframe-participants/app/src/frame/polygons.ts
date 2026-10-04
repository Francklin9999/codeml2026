import { OptiError, type Pt } from '../contracts';

/** Contour points closer than this to the previous kept point are dropped (mm). */
export const MIN_POINT_DIST_MM = 0.05;

/** Shoelace area: positive when the points turn counter-clockwise in a y-up frame. */
export function signedArea(pts: readonly Pt[]): number {
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x0, y0] = pts[i];
    const [x1, y1] = pts[(i + 1) % pts.length];
    a += x0 * y1 - x1 * y0;
  }
  return a / 2;
}

export function bbox(pts: readonly Pt[]): { minX: number; maxX: number; minY: number; maxY: number } {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const [x, y] of pts) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  return { minX, maxX, minY, maxY };
}

/** Validate and thin a raw contour: finite points, no point within 0.05 mm of its predecessor, at least 3 points left. */
export function cleanContour(raw: readonly Pt[]): Pt[] {
  const out: Pt[] = [];
  for (const p of raw) {
    if (!Array.isArray(p) || !Number.isFinite(p[0]) || !Number.isFinite(p[1])) throw new OptiError('NO_LENS', 'contour has a non-finite point');
    const last = out[out.length - 1];
    if (!last || Math.hypot(p[0] - last[0], p[1] - last[1]) >= MIN_POINT_DIST_MM) out.push([p[0], p[1]]);
  }
  // The closing edge may also be a duplicate.
  while (out.length > 1 && Math.hypot(out[0][0] - out[out.length - 1][0], out[0][1] - out[out.length - 1][1]) < MIN_POINT_DIST_MM) out.pop();
  if (out.length < 3 || Math.abs(signedArea(out)) < 1) throw new OptiError('NO_LENS', 'contour has fewer than 3 usable points or no area');
  return out;
}

export function rectPoly(x0: number, y0: number, x1: number, y1: number): Pt[] {
  return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
}
