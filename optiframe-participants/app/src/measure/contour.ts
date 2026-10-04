import { OptiError, type Mask, type Pt, type Rectified } from '../contracts';
import { polygonLength, signedArea } from './boxing';

/*
 * Which edge is measured: the OUTER boundary of the dark band that rings the lens (total internal
 * reflection at the rim on a backlit sheet). A calliper closes on the outer extent of the lens, so the
 * edge position is the outermost half-way crossing between the background level and the rim level
 * (strat2 4.4). The inner edge of the band is never used.
 *
 * DEVIATIONS FROM BRIEF 06 (flagged for the integrator; each was tested against the brief-literal variant
 * on the synthetic scenes of measure.test.ts: with the three changes below reverted, 4 of the 39 tests
 * miss the 0.05 mm bound, namely the three thin-ring cases (0.06 mm) and the sharp-corner rectangle (0.07 mm)):
 *  1. Step 2 says move to the outermost half-way crossing. Here the half-way crossing only locates the edge;
 *     the point is then moved to the steepest outward rise within 4 px of it (steepestNear). On a thin, blurred
 *     band the minimum is lifted and the half-way level drifts outwards, the steepest point does not.
 *  2. Step 3 says keep 30 harmonics. Here HARMONICS = 60: with 30, the sharp-corner rectangle (r = 1 mm,
 *     turned 8 deg) misses 0.05 mm (0.084 mm) even with restoreExtents.
 *  3. Not in the brief: restoreExtents rescales the low-passed curve so its extents equal parabola-fitted
 *     extremes of the unsmoothed curve, to undo the overshoot of the low-pass.
 * Known limit: a corner sharper than about r = 1 mm is still rounded by the low-pass; its effect on A and B
 * on real lenses is TO MEASURE.
 */

export const N_POINTS = 720;
export const HARMONICS = 60;
const SEARCH_MM = 1;          // profile half-length along the normal
const STEP_PX = 0.25;         // profile sampling step
const MIN_CONTRAST = 25;      // grey levels (0..255) between background and rim below which the point is not moved
const GRAD_WINDOW_PX = 4;     // how far from the half-way crossing the steepest point is looked for
const LOBE_FRAC = 0.85;
const GRAD_HALF_PX = 1;       // half-length of the derivative stencil
const EXTREMUM_FIT_MM = 1.2;  // half-length of the arc fitted around each of the four extremes (a parabola: exact for any radius >= 2 mm)
const MIN_AREA_MM2 = 100;     // smaller blobs are noise, not a lens

/** Crack-following trace: vertices are pixel corners, so the polygon edge lies on the mask boundary. */
function traceOuter(fg: Uint8Array, w: number, h: number, sx: number, sy: number): Pt[] {
  const on = (x: number, y: number) => x >= 0 && y >= 0 && x < w && y < h && fg[y * w + x] === 1;
  const DX = [1, 0, -1, 0];
  const DY = [0, 1, 0, -1];
  const pts: Pt[] = [[sx, sy]];
  let x = sx, y = sy, d = 0;
  for (let guard = 0; guard < 4 * w * h + 8; guard++) {
    x += DX[d];
    y += DY[d];
    let la: boolean, ra: boolean; // pixels ahead-left and ahead-right; foreground stays on the right
    if (d === 0) { la = on(x, y - 1); ra = on(x, y); }
    else if (d === 1) { la = on(x, y); ra = on(x - 1, y); }
    else if (d === 2) { la = on(x - 1, y); ra = on(x - 1, y - 1); }
    else { la = on(x - 1, y - 1); ra = on(x, y - 1); }
    const nd = !ra ? (d + 1) & 3 : la ? (d + 3) & 3 : d;
    if (x === sx && y === sy && nd === 0) return pts;
    if (nd !== d) pts.push([x, y]);
    d = nd;
  }
  throw new OptiError('NO_LENS', 'contour trace did not close');
}

/** Largest 4-connected component; returns its mask and its first pixel in raster order. */
function largestComponent(m: Mask): { fg: Uint8Array; sx: number; sy: number; area: number } | null {
  const { width: w, height: h, data } = m;
  const label = new Int32Array(w * h);
  const stack = new Int32Array(w * h);
  let best = 0, bestId = 0, bestStart = -1, id = 0;
  for (let i = 0; i < w * h; i++) {
    if (!data[i] || label[i]) continue;
    id++;
    let n = 0, sp = 0;
    stack[sp++] = i;
    label[i] = id;
    while (sp) {
      const p = stack[--sp];
      n++;
      const x = p % w;
      if (x > 0 && data[p - 1] && !label[p - 1]) { label[p - 1] = id; stack[sp++] = p - 1; }
      if (x < w - 1 && data[p + 1] && !label[p + 1]) { label[p + 1] = id; stack[sp++] = p + 1; }
      if (p >= w && data[p - w] && !label[p - w]) { label[p - w] = id; stack[sp++] = p - w; }
      if (p < w * (h - 1) && data[p + w] && !label[p + w]) { label[p + w] = id; stack[sp++] = p + w; }
    }
    if (n > best) { best = n; bestId = id; bestStart = i; }
  }
  if (!best) return null;
  const fg = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) if (label[i] === bestId) fg[i] = 1;
  return { fg, sx: bestStart % w, sy: Math.floor(bestStart / w), area: best };
}

export function resampleClosed(pts: Pt[], n: number): Pt[] {
  const m = pts.length;
  const cum = new Float64Array(m + 1);
  for (let i = 0; i < m; i++) {
    const a = pts[i], b = pts[(i + 1) % m];
    cum[i + 1] = cum[i] + Math.hypot(b[0] - a[0], b[1] - a[1]);
  }
  const total = cum[m];
  const out: Pt[] = [];
  let seg = 0;
  for (let k = 0; k < n; k++) {
    const s = (total * k) / n;
    while (seg < m - 1 && cum[seg + 1] <= s) seg++;
    const a = pts[seg], b = pts[(seg + 1) % m];
    const len = cum[seg + 1] - cum[seg];
    const t = len > 0 ? (s - cum[seg]) / len : 0;
    out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
  }
  return out;
}

/** Closed-curve low-pass: keep harmonics -K..K of x + iy. */
export function lowpassClosed(pts: Pt[], keep: number): Pt[] {
  const n = pts.length;
  const cos = new Float64Array(n), sin = new Float64Array(n);
  for (let i = 0; i < n; i++) { cos[i] = Math.cos((2 * Math.PI * i) / n); sin[i] = Math.sin((2 * Math.PI * i) / n); }
  const K = Math.min(keep, Math.floor((n - 1) / 2));
  const re: number[] = [], im: number[] = [];
  for (let k = -K; k <= K; k++) {
    let r = 0, q = 0;
    for (let j = 0; j < n; j++) {
      const idx = (((j * k) % n) + n) % n;
      const c = cos[idx], s = -sin[idx]; // e^{-i 2 pi jk / n}
      r += pts[j][0] * c - pts[j][1] * s;
      q += pts[j][0] * s + pts[j][1] * c;
    }
    re.push(r / n);
    im.push(q / n);
  }
  const out: Pt[] = [];
  for (let j = 0; j < n; j++) {
    let x = 0, y = 0;
    for (let k = -K; k <= K; k++) {
      const idx = (((j * k) % n) + n) % n;
      const c = cos[idx], s = sin[idx];
      x += re[k + K] * c - im[k + K] * s;
      y += re[k + K] * s + im[k + K] * c;
    }
    out.push([x, y]);
  }
  return out;
}

function greyOf(img: ImageData): Float32Array {
  const g = new Float32Array(img.width * img.height);
  const d = img.data;
  for (let i = 0; i < g.length; i++) g[i] = 0.299 * d[4 * i] + 0.587 * d[4 * i + 1] + 0.114 * d[4 * i + 2];
  return g;
}

/** Bilinear sample at crack coordinates (pixel i covers [i, i + 1), its centre is i + 0.5). */
function sample(g: Float32Array, w: number, h: number, x: number, y: number): number {
  const fx = Math.min(Math.max(x - 0.5, 0), w - 1), fy = Math.min(Math.max(y - 0.5, 0), h - 1);
  const x0 = Math.min(Math.floor(fx), w - 2 < 0 ? 0 : w - 2), y0 = Math.min(Math.floor(fy), h - 2 < 0 ? 0 : h - 2);
  const x1 = Math.min(x0 + 1, w - 1), y1 = Math.min(y0 + 1, h - 1);
  const tx = fx - x0, ty = fy - y0;
  return (g[y0 * w + x0] * (1 - tx) + g[y0 * w + x1] * tx) * (1 - ty) + (g[y1 * w + x0] * (1 - tx) + g[y1 * w + x1] * tx) * ty;
}

/**
 * Position of the steepest rise (towards the outside) near the half-way crossing s0, within GRAD_WINDOW_PX.
 * On a thin, blurred band the minimum is lifted and the half-way level drifts outwards; the steepest point
 * of the outer step does not, so it is the unbiased edge. Falls back to s0 when the profile is flat there.
 */
function steepestNear(sm: Float32Array, s0: number, sFirst: number): number {
  const n = sm.length;
  const d = Math.round(GRAD_HALF_PX / STEP_PX);
  const c0 = Math.round((s0 - sFirst) / STEP_PX);
  const reach = Math.round(GRAD_WINDOW_PX / STEP_PX);
  const grad = (c: number) => sm[Math.min(c + d, n - 1)] - sm[Math.max(c - d, 0)];
  let best = -Infinity, bc = c0;
  for (let c = Math.max(c0 - reach, 1); c <= Math.min(c0 + reach, n - 2); c++) {
    const g = grad(c);
    if (g > best) { best = g; bc = c; }
  }
  if (!(best > 0)) return s0;
  // centroid of the main lobe above LOBE_FRAC of its height: as unbiased as the peak, but a flat-topped lobe (blurred edge) does not make it jump with noise
  let lo = bc, hi = bc;
  while (lo > Math.max(c0 - reach, 1) && grad(lo - 1) >= LOBE_FRAC * best) lo--;
  while (hi < Math.min(c0 + reach, n - 2) && grad(hi + 1) >= LOBE_FRAC * best) hi++;
  let sw = 0, sc = 0;
  for (let c = lo; c <= hi; c++) { const g = grad(c); sw += g; sc += g * c; }
  return sFirst + (sc / sw) * STEP_PX;
}

/**
 * Move each point of a counter-clockwise pixel polygon to the outermost half-way crossing of the grey
 * profile along its outward normal. Points with too little contrast stay where the mask put them.
 */
export function refineSubpixel(poly: Pt[], img: ImageData, pxPerMm: number): Pt[] {
  const { width: w, height: h } = img;
  const g = greyOf(img);
  const per = polygonLength(poly);
  const dense = resampleClosed(poly, Math.max(64, Math.round(per))); // about one point per pixel
  const n = dense.length;
  const k = Math.max(2, Math.round(0.8 * pxPerMm));
  const nS = Math.round((2 * SEARCH_MM * pxPerMm) / STEP_PX) + 1;
  const sPos = (i: number) => -SEARCH_MM * pxPerMm + i * STEP_PX; // along the outward normal
  const prof = new Float32Array(nS), sm = new Float32Array(nS);
  return dense.map((p, i) => {
    const a = dense[(i - k + n) % n], b = dense[(i + k) % n];
    const tl = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const nx = (b[1] - a[1]) / tl, ny = -(b[0] - a[0]) / tl; // outward for counter-clockwise order
    for (let j = 0; j < nS; j++) prof[j] = sample(g, w, h, p[0] + nx * sPos(j), p[1] + ny * sPos(j));
    for (let j = 0; j < nS; j++) {
      const v = (c: number) => prof[Math.min(Math.max(c, 0), nS - 1)];
      sm[j] = (v(j - 2) + 4 * v(j - 1) + 6 * v(j) + 4 * v(j + 1) + v(j + 2)) / 16;
    }
    const nOut = Math.max(3, Math.round(nS * 0.15));
    let outside = 0, rim = Infinity;
    for (let j = nS - nOut; j < nS; j++) outside += sm[j] / nOut;
    for (let j = 0; j < nS; j++) if (sm[j] < rim) rim = sm[j];
    if (outside - rim < MIN_CONTRAST) return p;
    const half = (outside + rim) / 2;
    for (let j = nS - 1; j > 0; j--) {
      if (sm[j] > half && sm[j - 1] <= half) {
        const s0 = sPos(j) - ((sm[j] - half) / (sm[j] - sm[j - 1])) * STEP_PX;
        const s = steepestNear(sm, s0, sPos(0));
        return [p[0] + nx * s, p[1] + ny * s] as Pt;
      }
    }
    return p;
  });
}

function bounds(c: Pt[]): { x0: number; x1: number; y0: number; y1: number } {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const [x, y] of c) {
    if (x < x0) x0 = x;
    if (x > x1) x1 = x;
    if (y < y0) y0 = y;
    if (y > y1) y1 = y;
  }
  return { x0, x1, y0, y1 };
}

/**
 * Coordinate of the extreme of a noisy closed curve along one axis: a parabola fitted to the arc around the
 * point that is extreme in the smoothed curve. Reading the raw maximum would add the per-point noise to the
 * extent; a moving average would shave round corners.
 */
function extremum(dense: Pt[], smooth: Pt[], axis: 0 | 1, sign: 1 | -1): number {
  const n = dense.length;
  let ic = 0;
  for (let i = 1; i < n; i++) if (sign * smooth[i][axis] > sign * smooth[ic][axis]) ic = i;
  const per = polygonLength(dense);
  const K = Math.max(3, Math.min(20, Math.round((EXTREMUM_FIT_MM * n) / per)));
  const o = 1 - axis; // tangential coordinate
  const t0 = dense[ic][o];
  // least squares h = a + b t + c t^2 by normal equations on centred t
  let m0 = 0, m1 = 0, m2 = 0, m3 = 0, m4 = 0, r0 = 0, r1 = 0, r2 = 0, tmin = Infinity, tmax = -Infinity;
  for (let k = -K; k <= K; k++) {
    const p = dense[(ic + k + n) % n];
    const t = p[o] - t0, h = sign * p[axis];
    m0 += 1; m1 += t; m2 += t * t; m3 += t * t * t; m4 += t * t * t * t;
    r0 += h; r1 += h * t; r2 += h * t * t;
    if (t < tmin) tmin = t;
    if (t > tmax) tmax = t;
  }
  const det = (a: number[][]) => a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]);
  const M = [[m0, m1, m2], [m1, m2, m3], [m2, m3, m4]];
  const D = det(M);
  let best = -Infinity;
  if (Math.abs(D) > 1e-12 && tmax > tmin) {
    const sol = [0, 1, 2].map((col) => det(M.map((row, ri) => row.map((v, ci) => (ci === col ? [r0, r1, r2][ri] : v)))) / D);
    const f = (t: number) => sol[0] + sol[1] * t + sol[2] * t * t;
    best = Math.max(f(tmin), f(tmax));
    if (sol[2] < 0) best = Math.max(best, f(Math.min(Math.max(-sol[1] / (2 * sol[2]), tmin), tmax)));
  } else {
    best = r0 / m0;
  }
  return sign * best;
}

/**
 * A low-pass rounds corners and overshoots extrema (up to about 0.2 mm on a sharp corner), and A and B
 * are extents. Rescale the smoothed curve about its box centre so its extents equal those read on the contour it came from.
 */
function restoreExtents(smooth: Pt[], before: Pt[]): Pt[] {
  const s = bounds(smooth);
  const bx0 = extremum(before, smooth, 0, -1), bx1 = extremum(before, smooth, 0, 1);
  const by0 = extremum(before, smooth, 1, -1), by1 = extremum(before, smooth, 1, 1);
  const kx = s.x1 > s.x0 ? (bx1 - bx0) / (s.x1 - s.x0) : 1;
  const ky = s.y1 > s.y0 ? (by1 - by0) / (s.y1 - s.y0) : 1;
  const cx = (s.x0 + s.x1) / 2, cy = (s.y0 + s.y1) / 2;
  const bx = (bx0 + bx1) / 2, by = (by0 + by1) / 2;
  return smooth.map(([x, y]) => [bx + (x - cx) * kx, by + (y - cy) * ky] as Pt);
}

/** Mask + rectified image to a smooth counter-clockwise contour in mm: exactly N_POINTS points, lowpassed. */
export function contourFromMask(r: Rectified, m: Mask): Pt[] {
  const { width: w, height: h } = r.image;
  if (m.width !== w || m.height !== h || m.data.length !== w * h) throw new OptiError('LOAD_FAILED', 'mask and image sizes differ');
  const comp = largestComponent(m);
  if (!comp || comp.area / (r.pxPerMm * r.pxPerMm) < MIN_AREA_MM2) throw new OptiError('NO_LENS', 'mask is empty or too small');
  let poly = traceOuter(comp.fg, w, h, comp.sx, comp.sy);
  if (poly.some(([x, y]) => x <= 0 || y <= 0 || x >= w || y >= h)) throw new OptiError('LENS_OUT_OF_WINDOW', 'mask touches the window border');
  if (signedArea(poly) < 0) poly = poly.reverse();
  const refined = refineSubpixel(poly, r.image, r.pxPerMm).map(([x, y]) => [x / r.pxPerMm, y / r.pxPerMm] as Pt);
  const dense = resampleClosed(refined, N_POINTS);
  const smooth = restoreExtents(lowpassClosed(dense, HARMONICS), dense);
  return signedArea(smooth) < 0 ? smooth.reverse() : smooth;
}
