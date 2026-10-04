import { describe, it, expect } from 'vitest';
import { OptiError, type ErrorCode, type LensMeasurement, type Pt } from '../contracts';
import { fuseShots, messageFor, MAX_SPREAD_MM, MAX_CENTRE_SHIFT_MM } from './index';

const CODES: ErrorCode[] = ['NO_REFERENCE', 'REFERENCE_TILTED', 'BLURRY', 'NO_LENS', 'LENS_OUT_OF_WINDOW', 'GLARE',
  'INCONSISTENT_SHOTS', 'LENS_ROTATED', 'CAMERA_DENIED', 'LOAD_FAILED'];

function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}
const gauss = (r: () => number) => Math.sqrt(-2 * Math.log(1 - r())) * Math.cos(2 * Math.PI * r());

function shot(a: number, b: number, cx = 40, cy = 30, noise = 0, seed = 1): LensMeasurement {
  const r = rng(seed);
  const c: Pt[] = [];
  const n = 1440;
  for (let i = 0; i < n; i++) {
    const t = (2 * Math.PI * i) / n;
    const x = (a / 2) * Math.cos(t), y = (b / 2) * Math.sin(t);
    const len = Math.hypot(x, y) || 1;
    const k = noise ? (len + noise * gauss(r)) / len : 1;
    c.push([cx + x * k, cy + y * k]);
  }
  const xs = c.map(p => p[0]), ys = c.map(p => p[1]);
  const A = Math.max(...xs) - Math.min(...xs), B = Math.max(...ys) - Math.min(...ys);
  return { eye: 'R', contourMm: c, A, B, perimeter: 0, boxCentre: [cx, cy], method: 'classic',
    quality: { reprojErrMm: 0.1, sharpness: 100, nShots: 1, spreadA: 0, spreadB: 0 } };
}

describe('fuseShots', () => {
  it('returns a single shot unchanged', () => {
    const s = shot(50, 40);
    expect(fuseShots([s])).toBe(s);
  });

  it('fusing 5 noisy shots beats the mean single-shot error', () => {
    const shots = [1, 2, 3, 4, 5].map(i => shot(50, 40, 40, 30, 0.2, i * 7));
    const single = shots.map(s => (Math.abs(s.A - 50) + Math.abs(s.B - 40)) / 2);
    const meanSingle = single.reduce((a, b) => a + b, 0) / single.length;
    const f = fuseShots(shots);
    const fusedErr = (Math.abs(f.A - 50) + Math.abs(f.B - 40)) / 2;
    expect(fusedErr).toBeLessThan(meanSingle);
    expect(f.quality.nShots).toBe(5);
    expect(f.perimeter).toBeGreaterThan(0);
  });

  it('rejects a shot enlarged by 2 mm', () => {
    const good = [1, 2, 3, 4].map(i => shot(50, 40, 40, 30, 0.05, i));
    const ref = fuseShots(good);
    const f = fuseShots([...good, shot(52, 42, 40, 30, 0.05, 9)]);
    expect(f.quality.nShots).toBe(4);
    expect(Math.abs(f.A - ref.A)).toBeLessThan(0.05);
    expect(Math.abs(f.B - ref.B)).toBeLessThan(0.05);
  });

  it('throws INCONSISTENT_SHOTS when spread exceeds the limit', () => {
    const two = () => fuseShots([shot(50, 40), shot(50 + MAX_SPREAD_MM + 0.1, 40)]);
    expect(two).toThrow(OptiError);
    try { two(); } catch (e) { expect((e as OptiError).code).toBe('INCONSISTENT_SHOTS'); }
    expect(() => fuseShots([shot(50, 40), shot(50 + MAX_SPREAD_MM - 0.05, 40)])).not.toThrow();
  });

  it('throws INCONSISTENT_SHOTS when the lens moved, and not just below the limit', () => {
    const moved = () => fuseShots([shot(50, 40, 40, 30), shot(50, 40, 40 + MAX_CENTRE_SHIFT_MM + 0.1, 30)]);
    try { moved(); expect.unreachable(); } catch (e) { expect((e as OptiError).code).toBe('INCONSISTENT_SHOTS'); }
    expect(() => fuseShots([shot(50, 40, 40, 30), shot(50, 40, 40 + MAX_CENTRE_SHIFT_MM - 0.1, 30)])).not.toThrow();
  });

  it('reports spread and worst quality over kept shots', () => {
    const a = shot(50, 40), b = shot(50.4, 40.2);
    a.quality = { ...a.quality, reprojErrMm: 0.3, sharpness: 80 };
    const f = fuseShots([a, b]);
    expect(f.quality.spreadA).toBeCloseTo(0.4, 2);
    expect(f.quality.spreadB).toBeCloseTo(0.2, 2);
    expect(f.quality.reprojErrMm).toBe(0.3);
    expect(f.quality.sharpness).toBe(80);
  });
});

describe('messageFor', () => {
  it('has a French message for every ErrorCode', () => {
    for (const c of CODES) {
      const m = messageFor(c);
      expect(m.length).toBeGreaterThan(10);
      expect(m.split(/[.!?]\s/).length).toBeGreaterThanOrEqual(2);
    }
    expect(new Set(CODES.map(messageFor)).size).toBe(CODES.length);
  });
});
