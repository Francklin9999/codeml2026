import type { Pt } from '../contracts';

// 3x3 matrix, row-major, 9 numbers. Maps src points to dst points: dst ~ H * src.
export type Mat3 = number[];

export function applyH(H: Mat3, p: Pt): Pt {
  const w = H[6] * p[0] + H[7] * p[1] + H[8];
  return [(H[0] * p[0] + H[1] * p[1] + H[2]) / w, (H[3] * p[0] + H[4] * p[1] + H[5]) / w];
}

export function mul3(a: Mat3, b: Mat3): Mat3 {
  const r = new Array<number>(9).fill(0);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) for (let k = 0; k < 3; k++) r[i * 3 + j] += a[i * 3 + k] * b[k * 3 + j];
  return r;
}

export function invert3(m: Mat3): Mat3 | null {
  const [a, b, c, d, e, f, g, h, i] = m;
  const A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g;
  const det = a * A + b * B + c * C;
  if (!Number.isFinite(det) || Math.abs(det) < 1e-300) return null;
  const s = 1 / det;
  return [A * s, -(b * i - c * h) * s, (b * f - c * e) * s, B * s, (a * i - c * g) * s, -(a * f - c * d) * s, C * s, -(a * h - b * g) * s, (a * e - b * d) * s];
}

// Hartley normalisation: centroid at origin, mean distance sqrt(2). Returns T such that p' = T p.
function normaliser(pts: Pt[]): Mat3 {
  let cx = 0, cy = 0;
  for (const p of pts) { cx += p[0]; cy += p[1]; }
  cx /= pts.length; cy /= pts.length;
  let d = 0;
  for (const p of pts) d += Math.hypot(p[0] - cx, p[1] - cy);
  d /= pts.length;
  const s = d > 0 ? Math.SQRT2 / d : 1;
  return [s, 0, -s * cx, 0, s, -s * cy, 0, 0, 1];
}

// Eigen decomposition of a symmetric matrix (cyclic Jacobi). Returns eigenvalues and eigenvectors (columns of v).
function jacobiEigen(a: number[][], n: number): { values: number[]; vectors: number[][] } {
  const v: number[][] = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)));
  for (let sweep = 0; sweep < 60; sweep++) {
    let off = 0;
    for (let p = 0; p < n; p++) for (let q = p + 1; q < n; q++) off += a[p][q] * a[p][q];
    if (off < 1e-30) break;
    for (let p = 0; p < n; p++) {
      for (let q = p + 1; q < n; q++) {
        if (Math.abs(a[p][q]) < 1e-300) continue;
        const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
        const c = 1 / Math.sqrt(t * t + 1), s = t * c;
        for (let k = 0; k < n; k++) {
          const akp = a[k][p], akq = a[k][q];
          a[k][p] = c * akp - s * akq;
          a[k][q] = s * akp + c * akq;
        }
        for (let k = 0; k < n; k++) {
          const apk = a[p][k], aqk = a[q][k];
          a[p][k] = c * apk - s * aqk;
          a[q][k] = s * apk + c * aqk;
        }
        for (let k = 0; k < n; k++) {
          const vkp = v[k][p], vkq = v[k][q];
          v[k][p] = c * vkp - s * vkq;
          v[k][q] = s * vkp + c * vkq;
        }
      }
    }
  }
  return { values: a.map((row, i) => row[i]), vectors: v };
}

/** Least-squares homography (normalised DLT) from n >= 4 correspondences. Null when degenerate. */
export function fitHomography(src: Pt[], dst: Pt[]): Mat3 | null {
  const n = src.length;
  if (n < 4 || dst.length !== n) return null;
  const Ts = normaliser(src), Td = normaliser(dst);
  const ata = Array.from({ length: 9 }, () => new Array<number>(9).fill(0));
  const add = (r: number[]) => { for (let i = 0; i < 9; i++) for (let j = 0; j < 9; j++) ata[i][j] += r[i] * r[j]; };
  for (let k = 0; k < n; k++) {
    const [x, y] = applyAffine(Ts, src[k]);
    const [u, v] = applyAffine(Td, dst[k]);
    add([-x, -y, -1, 0, 0, 0, u * x, u * y, u]);
    add([0, 0, 0, -x, -y, -1, v * x, v * y, v]);
  }
  const { values, vectors } = jacobiEigen(ata, 9);
  const order = values.map((val, i) => i).sort((i, j) => values[i] - values[j]);
  // Degenerate (e.g. collinear points): the null space is more than one-dimensional.
  if (!(values[order[1]] > 1e-9 * Math.max(values[order[8]], 1e-300))) return null;
  const h = vectors.map((row) => row[order[0]]);
  const Hn = h;
  const Tdi = invert3(Td);
  if (!Tdi) return null;
  const H = mul3(mul3(Tdi, Hn), Ts);
  const s = Math.abs(H[8]) > 1e-12 ? 1 / H[8] : 1 / Math.hypot(...H);
  const out = H.map((x) => x * s);
  return out.every(Number.isFinite) ? out : null;
}

function applyAffine(T: Mat3, p: Pt): Pt {
  return [T[0] * p[0] + T[2], T[4] * p[1] + T[5]];
}

export interface RansacOptions {
  /** Inlier distance, in dst units. */
  threshold: number;
  maxIterations?: number;
  minInliers?: number;
  seed?: number;
}
export interface RansacResult { H: Mat3; inliers: boolean[]; nInliers: number; rms: number }

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function residuals(H: Mat3, src: Pt[], dst: Pt[]): number[] {
  return src.map((p, i) => {
    const q = applyH(H, p);
    return Math.hypot(q[0] - dst[i][0], q[1] - dst[i][1]);
  });
}

/** RANSAC on 4-point samples, then refit by least squares on the inliers until the inlier set is stable. */
export function ransacHomography(src: Pt[], dst: Pt[], opt: RansacOptions): RansacResult | null {
  const n = src.length;
  const minInliers = Math.max(4, opt.minInliers ?? 4);
  if (n < minInliers || dst.length !== n) return null;
  const rnd = mulberry32(opt.seed ?? 1);
  const maxIt = opt.maxIterations ?? 2000;
  let best: { H: Mat3; count: number; cost: number } | null = null;
  let need = maxIt;
  for (let it = 0; it < Math.min(need, maxIt); it++) {
    const idx = new Set<number>();
    while (idx.size < 4) idx.add(Math.floor(rnd() * n));
    const pick = [...idx];
    const H = fitHomography(pick.map((i) => src[i]), pick.map((i) => dst[i]));
    if (!H) continue;
    let count = 0, cost = 0;
    for (const r of residuals(H, src, dst)) {
      if (r <= opt.threshold) { count++; cost += r * r; }
    }
    if (!best || count > best.count || (count === best.count && cost < best.cost)) {
      best = { H, count, cost };
      const w = count / n;
      need = w >= 1 ? 0 : Math.ceil(Math.log(1 - 0.999) / Math.log(1 - w ** 4));
    }
  }
  if (!best || best.count < minInliers) return null;

  let H = best.H;
  let inliers = residuals(H, src, dst).map((r) => r <= opt.threshold);
  for (let round = 0; round < 5; round++) {
    const s = src.filter((_, i) => inliers[i]), d = dst.filter((_, i) => inliers[i]);
    const refit = fitHomography(s, d);
    if (!refit) break;
    H = refit;
    const next = residuals(H, src, dst).map((r) => r <= opt.threshold);
    const same = next.every((v, i) => v === inliers[i]);
    inliers = next;
    if (same) break;
  }
  const res = residuals(H, src, dst);
  const nInliers = inliers.filter(Boolean).length;
  if (nInliers < minInliers) return null;
  let sum = 0;
  res.forEach((r, i) => { if (inliers[i]) sum += r * r; });
  return { H, inliers, nInliers, rms: Math.sqrt(sum / nInliers) };
}
