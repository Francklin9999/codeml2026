import { describe, expect, it } from 'vitest';
import type { Pt } from '../contracts';
import { applyH, fitHomography, invert3, mul3, ransacHomography, type Mat3 } from './homography';

// Deterministic generator so a failure can be replayed.
function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

const TRUE_H: Mat3 = [8.2, 1.1, 640, -0.9, 8.5, 480, 2.1e-4, -1.3e-4, 1];

function grid(n: number, rand: () => number): Pt[] {
  const pts: Pt[] = [];
  for (let i = 0; i < n; i++) pts.push([-40 + rand() * 180, -30 + rand() * 150]);
  return pts;
}

function maxErr(H: Mat3, src: Pt[], dst: Pt[]): number {
  return Math.max(...src.map((p, i) => Math.hypot(applyH(H, p)[0] - dst[i][0], applyH(H, p)[1] - dst[i][1])));
}

describe('homography', () => {
  it('inverts and multiplies', () => {
    const inv = invert3(TRUE_H)!;
    const id = mul3(TRUE_H, inv);
    for (let i = 0; i < 9; i++) expect(id[i]).toBeCloseTo(i % 4 === 0 ? 1 : 0, 9);
    expect(invert3([1, 2, 3, 2, 4, 6, 1, 1, 1])).toBeNull();
  });

  it('recovers a homography from exact correspondences', () => {
    const rand = rng(7);
    const src = grid(16, rand);
    const dst = src.map((p) => applyH(TRUE_H, p));
    const H = fitHomography(src, dst)!;
    expect(H).not.toBeNull();
    expect(maxErr(H, src, dst)).toBeLessThan(1e-6);
    // Also on unseen points.
    const test = grid(50, rng(8));
    expect(maxErr(H, test, test.map((p) => applyH(TRUE_H, p)))).toBeLessThan(1e-5);
  });

  it('works with the minimum of four points and refuses collinear points', () => {
    const src: Pt[] = [[0, 0], [10, 0], [10, 10], [0, 10]];
    const dst = src.map((p) => applyH(TRUE_H, p));
    expect(maxErr(fitHomography(src, dst)!, src, dst)).toBeLessThan(1e-6);
    const line: Pt[] = [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]];
    expect(fitHomography(line, line)).toBeNull();
    expect(fitHomography(src.slice(0, 3), dst.slice(0, 3))).toBeNull();
  });

  it('RANSAC on exact correspondences flags every point as inlier', () => {
    const src = grid(30, rng(3));
    const dst = src.map((p) => applyH(TRUE_H, p));
    const r = ransacHomography(src, dst, { threshold: 0.5 })!;
    expect(r.nInliers).toBe(30);
    expect(r.rms).toBeLessThan(1e-6);
  });

  it('RANSAC with 20 % gross outliers recovers the model and flags the outliers', () => {
    const rand = rng(11);
    const n = 40;
    const src = grid(n, rand);
    const dst = src.map((p) => applyH(TRUE_H, p));
    const bad = new Set<number>();
    while (bad.size < n * 0.2) bad.add(Math.floor(rand() * n));
    for (const i of bad) dst[i] = [dst[i][0] + 40 + rand() * 300, dst[i][1] - 40 - rand() * 300];
    const r = ransacHomography(src, dst, { threshold: 0.5, seed: 5 })!;
    expect(r).not.toBeNull();
    expect(r.nInliers).toBe(n - bad.size);
    r.inliers.forEach((v, i) => expect(v).toBe(!bad.has(i)));
    const clean = src.filter((_, i) => !bad.has(i));
    expect(maxErr(r.H, clean, clean.map((p) => applyH(TRUE_H, p)))).toBeLessThan(1e-5);
  });

  it('RANSAC with 20 % outliers and small noise stays within the noise level', () => {
    const rand = rng(21);
    const n = 48;
    const src = grid(n, rand);
    const sigma = 0.2; // px
    const dst: Pt[] = src.map((p) => {
      const q = applyH(TRUE_H, p);
      return [q[0] + (rand() - 0.5) * 2 * sigma, q[1] + (rand() - 0.5) * 2 * sigma];
    });
    const bad = new Set<number>();
    while (bad.size < Math.round(n * 0.2)) bad.add(Math.floor(rand() * n));
    for (const i of bad) dst[i] = [dst[i][0] + 25 + rand() * 100, dst[i][1] + 25 + rand() * 100];
    const r = ransacHomography(src, dst, { threshold: 1.5, seed: 9 })!;
    expect(r.nInliers).toBe(n - bad.size);
    expect(r.rms).toBeLessThan(2 * sigma);
    const clean = src.filter((_, i) => !bad.has(i));
    expect(maxErr(r.H, clean, clean.map((p) => applyH(TRUE_H, p)))).toBeLessThan(3 * sigma);
  });

  it('RANSAC returns null when there is no consistent model', () => {
    const rand = rng(2);
    const src = grid(10, rand);
    const dst = grid(10, rand);
    expect(ransacHomography(src, dst, { threshold: 0.01, minInliers: 8 })).toBeNull();
  });
});
