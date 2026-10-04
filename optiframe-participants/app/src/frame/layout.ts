import type { FrameParams, Pt } from '../contracts';
import { bbox, rectPoly } from './polygons';

export const BRIDGE_BAR_H_MM = 4;
/** Bar centre above y = 0 (towards the top of the lenses). */
export const BRIDGE_BAR_RISE_MM = 3;
export const TENON_OVERLAP_MM = 1;

export interface Tenon {
  rect: Pt[];
  /** Hinge hole centre in the front view; the hole runs along y. */
  holeX: number;
  /** Extent of the block along y, used to size the hole cylinder. */
  yMin: number;
  yMax: number;
}

export interface Layout {
  /** Contours moved into frame coordinates (y down, bridge centre at x = 0, box centres at y = 0). */
  right: Pt[];
  left: Pt[];
  bridge: Pt[];
  tenons: Tenon[];
}

function translate(pts: readonly Pt[], dx: number, dy: number): Pt[] {
  return pts.map(([x, y]) => [x + dx, y + dy] as Pt);
}

/** Middle of the y range of the contour points lying within 0.3 mm of the extreme x: where the rim is most outward. */
function extremeY(pts: readonly Pt[], extremeX: number): number {
  let lo = Infinity, hi = -Infinity;
  for (const [x, y] of pts) {
    if (Math.abs(x - extremeX) <= 0.3) {
      if (y < lo) lo = y;
      if (y > hi) hi = y;
    }
  }
  return (lo + hi) / 2;
}

function tenonAt(contour: readonly Pt[], p: FrameParams, temporalIsMinX: boolean): Tenon {
  const bb = bbox(contour);
  const { w, h } = p.tenonMm;
  const reach = p.clearanceMm + p.rimWidthMm; // the outer rim sits this far beyond the contour extreme
  const cy = extremeY(contour, temporalIsMinX ? bb.minX : bb.maxX);
  const outerX = temporalIsMinX ? bb.minX - reach : bb.maxX + reach;
  const x0 = temporalIsMinX ? outerX + TENON_OVERLAP_MM - w : outerX - TENON_OVERLAP_MM;
  const x1 = x0 + w;
  return { rect: rectPoly(x0, cy - h / 2, x1, cy + h / 2), holeX: (x0 + x1) / 2, yMin: cy - h / 2, yMax: cy + h / 2 };
}

/**
 * Front view layout. `right` is the wearer's right lens (on the -x side, nasal edge = its max x),
 * `left` the left lens (on the +x side, nasal edge = its min x).
 */
export function layoutLenses(rightContour: readonly Pt[], leftContour: readonly Pt[], p: FrameParams): Layout {
  const rb = bbox(rightContour);
  const lb = bbox(leftContour);
  const right = translate(rightContour, -p.bridgeMm / 2 - rb.maxX, -(rb.minY + rb.maxY) / 2);
  const left = translate(leftContour, p.bridgeMm / 2 - lb.minX, -(lb.minY + lb.maxY) / 2);
  // The bar spans the nasal edges; lens openings are subtracted later, so it can only add rim material or bridge.
  const yc = -BRIDGE_BAR_RISE_MM;
  const bridge = rectPoly(-p.bridgeMm / 2, yc - BRIDGE_BAR_H_MM / 2, p.bridgeMm / 2, yc + BRIDGE_BAR_H_MM / 2);
  return { right, left, bridge, tenons: [tenonAt(right, p, true), tenonAt(left, p, false)] };
}
