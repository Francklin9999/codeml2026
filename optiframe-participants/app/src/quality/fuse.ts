import { OptiError, type LensMeasurement, type Pt } from '../contracts';

export const MAX_SPREAD_MM = 0.6;
/** Provisional, TO MEASURE on real hardware. */
export const MAX_CENTRE_SHIFT_MM = 1.0;
const N_ANGLES = 720;
const OUTLIER_MIN_MM = 0.3;

function median(v: number[]): number {
  const s = [...v].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** Extents along x and y, perimeter and box centre (same definition as the measure module). */
function geometry(c: Pt[]) {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity, perimeter = 0;
  for (let i = 0; i < c.length; i++) {
    const [x, y] = c[i];
    const [nx, ny] = c[(i + 1) % c.length];
    x0 = Math.min(x0, x); x1 = Math.max(x1, x);
    y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    perimeter += Math.hypot(nx - x, ny - y);
  }
  return { A: x1 - x0, B: y1 - y0, perimeter, boxCentre: [(x0 + x1) / 2, (y0 + y1) / 2] as Pt };
}

/** Farthest crossing of the ray from (cx,cy) at each angle with the polygon. */
function radii(c: Pt[], cx: number, cy: number): number[] {
  const out = new Array<number>(N_ANGLES).fill(0);
  for (let k = 0; k < N_ANGLES; k++) {
    const a = (2 * Math.PI * k) / N_ANGLES;
    const dx = Math.cos(a), dy = Math.sin(a);
    let best = 0;
    for (let i = 0; i < c.length; i++) {
      const [px, py] = c[i];
      const [qx, qy] = c[(i + 1) % c.length];
      const ex = qx - px, ey = qy - py;
      const den = dx * ey - dy * ex;
      if (Math.abs(den) < 1e-12) continue;
      const t = ((px - cx) * ey - (py - cy) * ex) / den;
      const u = ((px - cx) * dy - (py - cy) * dx) / den;
      if (t > best && u >= 0 && u <= 1) best = t;
    }
    out[k] = best;
  }
  return out;
}

function dropOutliers(shots: LensMeasurement[]): LensMeasurement[] {
  if (shots.length < 3) return shots;
  const mA = median(shots.map(s => s.A));
  const mB = median(shots.map(s => s.B));
  const tA = Math.max(OUTLIER_MIN_MM, 2.5 * median(shots.map(s => Math.abs(s.A - mA))));
  const tB = Math.max(OUTLIER_MIN_MM, 2.5 * median(shots.map(s => Math.abs(s.B - mB))));
  return shots.filter(s => Math.abs(s.A - mA) <= tA && Math.abs(s.B - mB) <= tB);
}

const range = (v: number[]) => Math.max(...v) - Math.min(...v);

export function fuseShots(shots: LensMeasurement[]): LensMeasurement {
  if (shots.length === 0) throw new OptiError('NO_LENS', 'no shot');
  if (shots.length === 1) return shots[0];

  const kept = dropOutliers(shots);
  const spreadA = range(kept.map(s => s.A));
  const spreadB = range(kept.map(s => s.B));
  if (spreadA > MAX_SPREAD_MM || spreadB > MAX_SPREAD_MM) {
    throw new OptiError('INCONSISTENT_SHOTS', `spread A ${spreadA.toFixed(2)} B ${spreadB.toFixed(2)} mm`);
  }
  const xs = kept.map(s => s.boxCentre[0]), ys = kept.map(s => s.boxCentre[1]);
  if (Math.hypot(range(xs), range(ys)) > MAX_CENTRE_SHIFT_MM) {
    // range-based diagonal is an upper bound of the largest pairwise distance; check exactly
    let maxD = 0;
    for (let i = 0; i < kept.length; i++)
      for (let j = i + 1; j < kept.length; j++)
        maxD = Math.max(maxD, Math.hypot(xs[i] - xs[j], ys[i] - ys[j]));
    if (maxD > MAX_CENTRE_SHIFT_MM) throw new OptiError('INCONSISTENT_SHOTS', `lens moved ${maxD.toFixed(2)} mm`);
  }

  const cx = xs.reduce((a, b) => a + b, 0) / xs.length;
  const cy = ys.reduce((a, b) => a + b, 0) / ys.length;
  const all = kept.map(s => radii(s.contourMm, cx, cy));
  const contourMm: Pt[] = [];
  for (let k = 0; k < N_ANGLES; k++) {
    const r = median(all.map(a => a[k]));
    const a = (2 * Math.PI * k) / N_ANGLES;
    contourMm.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  const g = geometry(contourMm);
  return {
    eye: kept[0].eye,
    contourMm,
    A: g.A, B: g.B, perimeter: g.perimeter, boxCentre: g.boxCentre,
    method: kept[0].method,
    quality: {
      reprojErrMm: Math.max(...kept.map(s => s.quality.reprojErrMm)),
      sharpness: Math.min(...kept.map(s => s.quality.sharpness)),
      nShots: kept.length,
      spreadA, spreadB,
    },
  };
}
