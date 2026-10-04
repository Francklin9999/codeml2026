import { afterEach, describe, expect, it, vi } from 'vitest';
import { OptiError, type Mask, type Pt, type Rectified } from '../contracts';
import { boxing, extentAlong, minAreaRect, polygonLength, signedArea } from './boxing';
import { EDGE_HEIGHT_MM, parallaxCorrect } from './correction';
import { loadBias, measureLens, rotationWarningDeg, setBias } from './index';

const PPM = 10;
const W_MM = 80, H_MM = 60;
const CX = 40, CY = 30;

const erf = (x: number) => {
  const t = 1 / (1 + 0.3275911 * Math.abs(x));
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return x >= 0 ? y : -y;
};

/** Signed distance (mm, negative inside) to a shape centred at (CX, CY). */
type Sdf = (x: number, y: number) => number;
const ellipseSdf = (a: number, b: number, rot = 0): Sdf => (x, y) => {
  const dx = x - CX, dy = y - CY, c = Math.cos(rot), s = Math.sin(rot);
  const u = dx * c + dy * s, v = -dx * s + dy * c;
  const f = (u / a) ** 2 + (v / b) ** 2;
  const g = Math.hypot((2 * u) / (a * a), (2 * v) / (b * b));
  return (f - 1) / (g || 1); // first-order distance, exact enough near the edge
};
const roundRectSdf = (w: number, h: number, r: number, rot = 0): Sdf => (x0, y0) => {
  const dx = x0 - CX, dy = y0 - CY, c = Math.cos(rot), s = Math.sin(rot);
  const x = CX + dx * c + dy * s, y = CY - dx * s + dy * c; // point in the frame of the rectangle
  const qx = Math.abs(x - CX) - (w / 2 - r), qy = Math.abs(y - CY) - (h / 2 - r);
  return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r;
};

interface Scene { r: Rectified; mask: Mask }
/**
 * Backlit lens: bright background, dark band of width bandMm inside the outer edge, brighter lens interior,
 * all blurred by sigma (erf profile). The mask is the true shape grown by maskGrowMm (a loose mask).
 */
function scene(sdf: Sdf, opts: { maskGrowMm?: number; sigmaMm?: number; bandMm?: number; noise?: number; cameraDistMm?: number; bg?: number; dark?: number } = {}): Scene {
  const { maskGrowMm = 0, sigmaMm = 0.3, bandMm = 1.5, noise = 0, cameraDistMm, bg = 230, dark = 40 } = opts;
  const w = W_MM * PPM, h = H_MM * PPM;
  const img = new ImageData(w, h);
  const mask = new Uint8Array(w * h);
  let seed = 12345;
  const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296) - 0.5;
  const S = (u: number) => 0.5 * (1 + erf(u / (sigmaMm * Math.SQRT2)));
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < w; i++) {
      const d = sdf((i + 0.5) / PPM, (j + 0.5) / PPM);
      const v = bg + (dark - bg) * S(-d) + (200 - dark) * S(-d - bandMm) + noise * rnd();
      const k = 4 * (j * w + i);
      img.data[k] = img.data[k + 1] = img.data[k + 2] = Math.max(0, Math.min(255, v));
      img.data[k + 3] = 255;
      if (d <= maskGrowMm) mask[j * w + i] = 1;
    }
  }
  return {
    r: { image: img, pxPerMm: PPM, H: [1, 0, 0, 0, 1, 0, 0, 0, 1], reprojErrMm: 0.07, sharpness: 42, cameraDistMm },
    mask: { data: mask, width: w, height: h, method: 'classic', score: 1 },
  };
}

const ramanujan = (a: number, b: number) => Math.PI * (3 * (a + b) - Math.sqrt((3 * a + b) * (a + 3 * b)));
/** Closed-form extents and perimeter of a w x h rectangle with corner radius r turned by deg degrees. */
const roundRectTruth = (w: number, h: number, r: number, deg: number) => {
  const c = Math.abs(Math.cos((deg * Math.PI) / 180)), s = Math.abs(Math.sin((deg * Math.PI) / 180));
  return { A: (w - 2 * r) * c + (h - 2 * r) * s + 2 * r, B: (w - 2 * r) * s + (h - 2 * r) * c + 2 * r, per: 2 * (w - 2 * r) + 2 * (h - 2 * r) + 2 * Math.PI * r };
};
const rotRect = (w: number, h: number, phi: number): Pt[] => {
  const c = Math.cos(phi), s = Math.sin(phi);
  return ([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]] as Pt[]).map(([x, y]) => [x * c - y * s + 50, x * s + y * c + 40] as Pt);
};

afterEach(() => { setBias(); vi.unstubAllGlobals(); });

describe('measureLens on a blurred dark ring of known outer size', () => {
  const shapes: [string, Sdf, number, number, number][] = [
    ['ellipse 52 x 38', ellipseSdf(26, 19), 52, 38, ramanujan(26, 19)],
    ['circle 46', ellipseSdf(23, 23), 46, 46, 2 * Math.PI * 23],
    ['rounded rectangle 50 x 36, r = 10', roundRectSdf(50, 36, 10), 50, 36, 2 * (30 + 16) + 2 * Math.PI * 10],
  ];
  for (const [name, sdf, A, B, per] of shapes) {
    for (const grow of [0, 0.4, -0.3]) {
      it(`${name}, mask off by ${grow} mm`, () => {
        const { r, mask } = scene(sdf, { maskGrowMm: grow, noise: 6 });
        const m = measureLens(r, mask, 'R');
        expect(Math.abs(m.A - A)).toBeLessThan(0.05);
        expect(Math.abs(m.B - B)).toBeLessThan(0.05);
        expect(Math.abs(m.perimeter - per) / per).toBeLessThan(0.003);
        expect(m.contourMm).toHaveLength(720);
        expect(signedArea(m.contourMm)).toBeGreaterThan(0);
        expect(m.boxCentre[0]).toBeCloseTo(CX, 1);
        expect(m.boxCentre[1]).toBeCloseTo(CY, 1);
      });
    }
  }

  // Thin ring, strong blur: ring 0.5 mm (5 px) and sigma 1.5 px. The outer step is read at its steepest point,
  // not at half-way to the lifted minimum of the band, which would sit about 0.06 mm outside.
  for (const grow of [0, 0.4, -0.3]) {
    it(`thin ring 0.5 mm, sigma 1.5 px, rounded rectangle 52 x 34, r = 8, mask off by ${grow} mm`, () => {
      const t = roundRectTruth(52, 34, 8, 0);
      const { r, mask } = scene(roundRectSdf(52, 34, 8), { maskGrowMm: grow, bandMm: 0.5, sigmaMm: 0.15, noise: 6 });
      const m = measureLens(r, mask, 'R');
      expect(Math.abs(m.A - t.A)).toBeLessThan(0.05);
      expect(Math.abs(m.B - t.B)).toBeLessThan(0.05);
      expect(Math.abs(m.perimeter - t.per) / t.per).toBeLessThan(0.003);
    });
  }

  // Turned rectangles with small corner radii: the extents sit on the corner arcs, where a low-pass would overshoot
  // or clip. Corners of 1 mm radius and more are covered; sharper ones are TO MEASURE (see contour.ts).
  const turned: [number, number, number, number, number, number][] = [
    // w, h, r, deg, band, sigma
    [50, 34, 3, 8, 1.5, 0.3], [50, 34, 3, 20, 0.5, 0.15], [50, 34, 5, 8, 0.5, 0.15], [50, 34, 5, 30, 1.5, 0.3], [50, 34, 4, 0, 1.5, 0.3], [50, 34, 1, 8, 1.5, 0.3],
  ];
  for (const [w, h, rad, deg, band, sig] of turned) {
    it(`rectangle ${w} x ${h}, r = ${rad}, turned ${deg} deg, ring ${band} mm, sigma ${sig} mm`, () => {
      const t = roundRectTruth(w, h, rad, deg);
      const { r, mask } = scene(roundRectSdf(w, h, rad, (deg * Math.PI) / 180), { bandMm: band, sigmaMm: sig, noise: 6 });
      const m = measureLens(r, mask, 'R');
      const tol = 0.05;
      expect(Math.abs(m.A - t.A)).toBeLessThan(tol);
      expect(Math.abs(m.B - t.B)).toBeLessThan(tol);
      expect(Math.abs(m.perimeter - t.per) / t.per).toBeLessThan(0.003);
      expect(Math.abs(extentAlong(m.contourMm, 0) - m.A)).toBeLessThan(1e-9);
    });
  }

  it('fills quality from Rectified and the eye and method from the inputs', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    const m = measureLens(r, mask, 'L');
    expect(m.eye).toBe('L');
    expect(m.method).toBe('classic');
    expect(m.quality).toEqual({ reprojErrMm: 0.07, sharpness: 42, nShots: 1, spreadA: 0, spreadB: 0 });
  });

  it('keeps the mask edge when the profile has no contrast', () => {
    const { r, mask } = scene(ellipseSdf(26, 19), { bg: 120, dark: 110 });
    const m = measureLens(r, mask, 'R');
    expect(Math.abs(m.A - 52)).toBeLessThan(0.15); // pixel-grid accuracy only
  });

  it('ignores a small speck far from the lens', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    for (let j = 20; j < 60; j++) for (let i = 20; i < 60; i++) mask.data[j * mask.width + i] = 1;
    expect(Math.abs(measureLens(r, mask, 'R').A - 52)).toBeLessThan(0.05);
  });
});

describe('errors', () => {
  it('empty mask: NO_LENS', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    mask.data.fill(0);
    expect(() => measureLens(r, mask, 'R')).toThrow(expect.objectContaining({ code: 'NO_LENS' }));
  });
  it('mask touching the window border: LENS_OUT_OF_WINDOW', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    mask.data.fill(1);
    expect(() => measureLens(r, mask, 'R')).toThrow(expect.objectContaining({ code: 'LENS_OUT_OF_WINDOW' }));
  });
  it('size mismatch is an OptiError', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    const bad: Mask = { ...mask, width: mask.width - 1 };
    expect(() => measureLens(r, bad, 'R')).toThrow(OptiError);
  });
});

describe('boxing and extentAlong', () => {
  it('rotated rectangle: closed form', () => {
    const w = 52, h = 38;
    for (const deg of [0, 5, 12, 30, 45, 80]) {
      const phi = (deg * Math.PI) / 180;
      const c = rotRect(w, h, phi);
      const b = boxing(c);
      expect(b.A).toBeCloseTo(w * Math.abs(Math.cos(phi)) + h * Math.abs(Math.sin(phi)), 9);
      expect(b.B).toBeCloseTo(w * Math.abs(Math.sin(phi)) + h * Math.abs(Math.cos(phi)), 9);
      expect(b.perimeter).toBeCloseTo(2 * (w + h), 9);
      expect(b.boxCentre[0]).toBeCloseTo(50, 9);
      expect(b.boxCentre[1]).toBeCloseTo(40, 9);
      expect(extentAlong(c, phi)).toBeCloseTo(w, 9); // calliper turned with the rectangle
      expect(extentAlong(c, phi + Math.PI / 2)).toBeCloseTo(h, 9);
    }
  });
  it('ellipse: A = 2a, B = 2b, perimeter by Ramanujan', () => {
    const a = 26, b = 19;
    const c: Pt[] = Array.from({ length: 4000 }, (_, i) => [a * Math.cos((2 * Math.PI * i) / 4000), b * Math.sin((2 * Math.PI * i) / 4000)] as Pt);
    const m = boxing(c);
    expect(m.A).toBeCloseTo(2 * a, 5);
    expect(m.B).toBeCloseTo(2 * b, 5);
    expect(Math.abs(m.perimeter - ramanujan(a, b)) / ramanujan(a, b)).toBeLessThan(1e-4);
    expect(polygonLength(c)).toBe(m.perimeter);
  });
  it('minimum-area rectangle recovers size and angle of a rotated rectangle', () => {
    const r = minAreaRect(rotRect(52, 38, (12 * Math.PI) / 180));
    expect(r.long).toBeCloseTo(52, 6);
    expect(r.short).toBeCloseTo(38, 6);
    expect(r.longAngleDeg).toBeCloseTo(12, 6);
    expect(minAreaRect(rotRect(52, 38, (-20 * Math.PI) / 180)).longAngleDeg).toBeCloseTo(-20, 6);
  });
});

describe('rotationWarningDeg', () => {
  const asMeasurement = (contourMm: Pt[]) => {
    const b = boxing(contourMm);
    return { eye: 'R' as const, contourMm, ...b, method: 'classic' as const, quality: { reprojErrMm: 0, sharpness: 0, nShots: 1, spreadA: 0, spreadB: 0 } };
  };
  it('null when aligned, the angle when turned more than 5 degrees', () => {
    expect(rotationWarningDeg(asMeasurement(rotRect(52, 38, (3 * Math.PI) / 180)))).toBeNull();
    expect(rotationWarningDeg(asMeasurement(rotRect(52, 38, 0)))).toBeNull();
    expect(rotationWarningDeg(asMeasurement(rotRect(52, 38, (8 * Math.PI) / 180)))).toBeCloseTo(8, 6);
    expect(rotationWarningDeg(asMeasurement(rotRect(52, 38, (-40 * Math.PI) / 180)))).toBeCloseTo(40, 6);
  });
  it('null for a near-circular shape whatever its orientation', () => {
    const c: Pt[] = Array.from({ length: 360 }, (_, i) => [50 + 20 * Math.cos((i * Math.PI) / 180), 40 + 20.5 * Math.sin((i * Math.PI) / 180)] as Pt);
    expect(rotationWarningDeg(asMeasurement(c))).toBeNull();
  });
  it('works on a measured ellipse turned by 15 degrees', () => {
    const { r, mask } = scene(ellipseSdf(26, 19, (15 * Math.PI) / 180));
    const w = rotationWarningDeg(measureLens(r, mask, 'R'));
    expect(w).not.toBeNull();
    expect(w as number).toBeGreaterThan(12);
    expect(w as number).toBeLessThan(18);
  });
});

describe('parallax', () => {
  it('D = 300, h = 3 scales about the window centre by 0.99', () => {
    expect(EDGE_HEIGHT_MM).toBe(3);
    const out = parallaxCorrect([[10, 10], [40, 30], [70, 50]], 300, { w: 80, h: 60 });
    expect(out[0][0]).toBeCloseTo(40 - 30 * 0.99, 12);
    expect(out[0][1]).toBeCloseTo(30 - 20 * 0.99, 12);
    expect(out[1]).toEqual([40, 30]);
    expect(out[2][0]).toBeCloseTo(40 + 30 * 0.99, 12);
  });
  it('no scaling when D is unknown or implausible', () => {
    const c: Pt[] = [[1, 2], [3, 4]];
    expect(parallaxCorrect(c, undefined, { w: 80, h: 60 })).toBe(c);
    expect(parallaxCorrect(c, 2, { w: 80, h: 60 })).toBe(c);
    expect(parallaxCorrect(c, NaN, { w: 80, h: 60 })).toBe(c);
  });
  it('measureLens uses cameraDistMm: extents shrink by 1 % at D = 300', () => {
    const base = scene(ellipseSdf(26, 19));
    const a0 = measureLens(base.r, base.mask, 'R');
    const a1 = measureLens({ ...base.r, cameraDistMm: 300 }, base.mask, 'R');
    expect(a1.A / a0.A).toBeCloseTo(0.99, 5);
    expect(a1.B / a0.B).toBeCloseTo(0.99, 5);
  });
});

describe('bias', () => {
  it('the contour extents equal the reported A and B, and the perimeter follows the contour', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    const base = measureLens(r, mask, 'R');
    setBias({ a0: 0.4, a1: 1.01, b0: -0.3, b1: 0.995 });
    const m = measureLens(r, mask, 'R');
    expect(m.A).toBeCloseTo(0.4 + 1.01 * base.A, 9);
    expect(m.B).toBeCloseTo(-0.3 + 0.995 * base.B, 9);
    expect(Math.abs(extentAlong(m.contourMm, 0) - m.A)).toBeLessThan(0.01);
    expect(Math.abs(extentAlong(m.contourMm, Math.PI / 2) - m.B)).toBeLessThan(0.01);
    expect(m.perimeter).toBeCloseTo(polygonLength(m.contourMm), 9);
    expect(m.boxCentre[0]).toBeCloseTo(base.boxCentre[0], 9);
    expect(m.boxCentre[1]).toBeCloseTo(base.boxCentre[1], 9);
    expect(m.contourMm).toHaveLength(720);
  });
  it('identity by default, and setBias() resets', () => {
    const { r, mask } = scene(ellipseSdf(26, 19));
    const a = measureLens(r, mask, 'R').A;
    setBias({ a0: 1, a1: 1, b0: 0, b1: 1 });
    expect(measureLens(r, mask, 'R').A).toBeCloseTo(a + 1, 9);
    setBias();
    expect(measureLens(r, mask, 'R').A).toBeCloseTo(a, 9);
  });
  it('rejects a broken bias', () => {
    expect(() => setBias({ a0: 0, a1: 0, b0: 0, b1: 1 })).toThrow(OptiError);
    expect(() => setBias({ a0: NaN, a1: 1, b0: 0, b1: 1 })).toThrow(OptiError);
  });
  it('loadBias reads the four numbers and ignores extra keys', async () => {
    const body = { a0: 0.2, a1: 1, b0: 0, b1: 1, fittedOn: '2026-10-03', nLenses: 8, phones: ['x'], loMaeBefore: 0.6, loMaeAfter: 0.3, helps: true };
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => body })));
    await loadBias('bias.json');
    const { r, mask } = scene(ellipseSdf(26, 19));
    setBias(); // reset then reload to prove the loader sets it
    await loadBias('bias.json');
    expect(measureLens(r, mask, 'R').A).toBeGreaterThan(52.15);
  });
  it('loadBias: bad answer is LOAD_FAILED', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 404, json: async () => ({}) })));
    await expect(loadBias('bias.json')).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ a0: 'x' }) })));
    await expect(loadBias('bias.json')).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => null })));
    await expect(loadBias('bias.json')).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => 42 })));
    await expect(loadBias('bias.json')).rejects.toMatchObject({ code: 'LOAD_FAILED' });
  });
  it('the shipped bias.json is the identity', async () => {
    const { readFileSync } = await import('node:fs');
    const j = JSON.parse(readFileSync(new URL('../../public/bias.json', import.meta.url), 'utf8'));
    expect([j.a0, j.a1, j.b0, j.b1]).toEqual([0, 1, 0, 1]);
  });
});
