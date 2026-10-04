import { describe, expect, it, vi } from 'vitest';
import { OptiError, type Rectified } from '../contracts';
import { MIN_RIM_CONTRAST, segmentClassic } from './segmentClassic';

// Rendering a 800x650 synthetic window per test is slow on a loaded machine.
vi.setConfig({ testTimeout: 60000 });

// ---- synthetic rectified windows (80 x 65 mm at 10 px/mm unless stated) -------------------------

const WIN_W_MM = 80, WIN_H_MM = 65;

type Sd = (x: number, y: number) => number; // signed distance in mm, negative inside

function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** First-order distance to an ellipse: exact on the boundary, close to it within a few mm. */
const ellipse = (cx: number, cy: number, a: number, b: number): Sd => (x, y) => {
  const dx = x - cx, dy = y - cy;
  const f = (dx * dx) / (a * a) + (dy * dy) / (b * b) - 1;
  const g = Math.hypot((2 * dx) / (a * a), (2 * dy) / (b * b));
  return g < 1e-9 ? -Math.min(a, b) : f / g;
};

const roundedBox = (cx: number, cy: number, hw: number, hh: number, rad: number): Sd => (x, y) => {
  const qx = Math.abs(x - cx) - hw + rad, qy = Math.abs(y - cy) - hh + rad;
  return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - rad;
};

const circle = (cx: number, cy: number, rad: number): Sd => (x, y) => Math.hypot(x - cx, y - cy) - rad;
const minus = (s: Sd, hole: Sd): Sd => (x, y) => Math.max(s(x, y), -hole(x, y));

interface Scene {
  shape: Sd;
  style: 'ring' | 'filled';
  ringMm?: number; // ring thickness
  contrast?: number; // darkness of the rim / tint as a share of the background
  edgeBlurMm?: number; // soft edge of a filled shape
  ppm?: number;
  specks?: boolean;
  noise?: number; // grey levels
  glareDisc?: { cx: number; cy: number; rad: number };
  seed?: number;
}

function render(s: Scene): { rect: Rectified; truth: Uint8Array } {
  const ppm = s.ppm ?? 10, w = Math.round(WIN_W_MM * ppm), h = Math.round(WIN_H_MM * ppm);
  const rnd = mulberry32(s.seed ?? 7);
  const gauss = () => Math.sqrt(-2 * Math.log(1 - rnd())) * Math.cos(2 * Math.PI * rnd());
  const cover = (d: number, widthMm = 1 / ppm) => Math.min(1, Math.max(0, 0.5 - d / widthMm));
  const contrast = s.contrast ?? 0.7, ringMm = s.ringMm ?? 1, noise = s.noise ?? 3;

  const specks: [number, number, number][] = []; // cx, cy, radius in mm
  if (s.specks !== false) {
    for (let i = 0; i < 30; i++) specks.push([2 + rnd() * 76, 2 + rnd() * 61, 0.15 + rnd() * 0.4]);
    specks.push([8, 8, 1.4], [72, 55, 1.4]); // two bigger blobs, each alone
  }
  const scratchA: [number, number] = [20, 56], scratchB: [number, number] = [26, 58];

  const rgba = new Uint8ClampedArray(w * h * 4), truth = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const mx = (x + 0.5) / ppm, my = (y + 0.5) / ppm;
      const sd = s.shape(mx, my);
      let t = 1;
      if (s.style === 'ring') {
        const ringCov = cover(sd) - cover(sd + ringMm);
        t -= contrast * ringCov;
      } else {
        t -= contrast * cover(sd, s.edgeBlurMm ?? 1 / ppm);
      }
      for (const [sx, sy, sr] of specks) {
        if (Math.abs(mx - sx) > sr + 1 || Math.abs(my - sy) > sr + 1) continue;
        t = Math.min(t, 1 - 0.7 * cover(Math.hypot(mx - sx, my - sy) - sr));
      }
      // scratch: thin line, 0.2 mm wide
      if (s.specks !== false && mx > 18 && mx < 28 && my > 54 && my < 60) {
        const vx = scratchB[0] - scratchA[0], vy = scratchB[1] - scratchA[1];
        const u = Math.min(1, Math.max(0, ((mx - scratchA[0]) * vx + (my - scratchA[1]) * vy) / (vx * vx + vy * vy)));
        t = Math.min(t, 1 - 0.3 * cover(Math.hypot(mx - scratchA[0] - u * vx, my - scratchA[1] - u * vy) - 0.1));
      }
      // uneven backlight: 12 % across, 5 % down
      const light = 200 * (1 + 0.12 * ((2 * x) / w - 1) + 0.05 * ((2 * y) / h - 1));
      let v = light * t + gauss() * noise;
      if (s.glareDisc && Math.hypot(mx - s.glareDisc.cx, my - s.glareDisc.cy) < s.glareDisc.rad) v = 255;
      const o = (y * w + x) * 4;
      rgba[o] = rgba[o + 1] = rgba[o + 2] = v;
      rgba[o + 3] = 255;
      truth[y * w + x] = sd <= 0 ? 1 : 0;
    }
  }
  const rect: Rectified = { image: new ImageData(rgba, w, h), pxPerMm: ppm, H: [1, 0, 0, 0, 1, 0, 0, 0, 1], reprojErrMm: 0, sharpness: 1 };
  return { rect, truth };
}

function iou(a: Uint8Array, b: Uint8Array): number {
  let i = 0, u = 0;
  for (let k = 0; k < a.length; k++) { if (a[k] && b[k]) i++; if (a[k] || b[k]) u++; }
  return i / u;
}

function codeOf(fn: () => unknown): string {
  try { fn(); } catch (e) { return e instanceof OptiError ? e.code : 'OTHER:' + String(e); }
  return 'NO_ERROR';
}

const lens = ellipse(40, 32, 25, 18); // 50 x 36 mm
const box = roundedBox(40, 32, 26, 17, 9); // 52 x 34 mm

// ---- the required cases --------------------------------------------------------------------------

describe('segmentClassic, backlit lens (dark rim on bright background)', () => {
  it('ellipse 50x36 with a 1 mm ring, gradient light, noise and dust: IoU >= 0.98', () => {
    const { rect, truth } = render({ shape: lens, style: 'ring' });
    const m = segmentClassic(rect);
    expect(m.method).toBe('classic');
    expect(m.width).toBe(800);
    expect(m.height).toBe(650);
    expect(m.data.length).toBe(800 * 650);
    expect(m.score).toBeGreaterThan(0);
    expect(m.score).toBeLessThanOrEqual(1);
    expect(iou(m.data, truth)).toBeGreaterThanOrEqual(0.98);
  });

  it('rounded rectangle 52x34: IoU >= 0.98', () => {
    const { rect, truth } = render({ shape: box, style: 'ring', seed: 11 });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.98);
  });

  it('works at another resolution (5 px/mm): sizes are in mm', () => {
    const { rect, truth } = render({ shape: lens, style: 'ring', ppm: 5, seed: 3 });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.97);
  });

  it('thick dark band (high minus, 4 mm): measures the outer boundary', () => {
    const { rect, truth } = render({ shape: ellipse(40, 32, 26, 19), style: 'ring', ringMm: 4, seed: 5 });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.98);
  });

  it('dust and scratches over the lens and the ring do not change the outline', () => {
    const dusty = ellipse(40, 32, 25, 18);
    const { rect, truth } = render({ shape: dusty, style: 'ring', seed: 21 });
    // one more large speck stuck to the outside of the ring
    const d = rect.image.data;
    for (let y = 0; y < 650; y++) for (let x = 0; x < 800; x++) {
      if (Math.hypot(x + 0.5 - 665, y + 0.5 - 320) < 5) d[(y * 800 + x) * 4] = d[(y * 800 + x) * 4 + 1] = d[(y * 800 + x) * 4 + 2] = 40;
    }
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.98);
  });

  it('small notch (about 2 mm deep) passes the solidity gate and stays in the outline', () => {
    const notched = minus(lens, circle(40 + 25 + 0.5, 32, 2.5)); // about 2 mm deep at the right edge
    const { rect, truth } = render({ shape: notched, style: 'ring', seed: 9 });
    const m = segmentClassic(rect);
    expect(iou(m.data, truth)).toBeGreaterThanOrEqual(0.98);
    // the notch itself is background
    expect(m.data[320 * 800 + 648]).toBe(0);
  });
});

describe('segmentClassic, tinted lens (filled dark shape)', () => {
  it('filled dark ellipse passes', () => {
    const { rect, truth } = render({ shape: lens, style: 'filled', contrast: 0.55, seed: 4 });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.98);
  });

  it('light tint with a soft edge falls back to plain thresholding', () => {
    const { rect, truth } = render({ shape: lens, style: 'filled', contrast: 0.3, edgeBlurMm: 1.6, seed: 6 });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.97);
  });
});

describe('segmentClassic, error codes', () => {
  it('NO_LENS on an empty window (noise only)', () => {
    const { rect } = render({ shape: () => 100, style: 'ring', specks: false });
    expect(codeOf(() => segmentClassic(rect))).toBe('NO_LENS');
  });

  it('NO_LENS on an empty window with dust only', () => {
    const { rect } = render({ shape: () => 100, style: 'ring' });
    expect(codeOf(() => segmentClassic(rect))).toBe('NO_LENS');
  });

  it('NO_LENS when the object is too small to be a lens', () => {
    const { rect } = render({ shape: ellipse(40, 32, 10, 7), style: 'ring' });
    expect(codeOf(() => segmentClassic(rect))).toBe('NO_LENS');
  });

  it('NO_LENS when the rim is fainter than MIN_RIM_CONTRAST (high plus lens)', () => {
    expect(MIN_RIM_CONTRAST).toBeGreaterThan(0.04);
    const { rect } = render({ shape: lens, style: 'ring', contrast: 0.04 });
    expect(codeOf(() => segmentClassic(rect))).toBe('NO_LENS');
  });

  it('a rim just above MIN_RIM_CONTRAST is still found', () => {
    const { rect, truth } = render({ shape: lens, style: 'ring', contrast: 0.3, seed: 8 });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.97);
  });

  it('LENS_OUT_OF_WINDOW when the ring is cut by the window border', () => {
    const { rect } = render({ shape: ellipse(62, 32, 25, 18), style: 'ring' });
    expect(codeOf(() => segmentClassic(rect))).toBe('LENS_OUT_OF_WINDOW');
  });

  it('LENS_OUT_OF_WINDOW when a tinted lens is cut by the window border', () => {
    const { rect } = render({ shape: ellipse(40, 8, 25, 18), style: 'filled', contrast: 0.55 });
    expect(codeOf(() => segmentClassic(rect))).toBe('LENS_OUT_OF_WINDOW');
  });

  it('GLARE when more than 5 % of the lens is saturated', () => {
    const { rect } = render({ shape: lens, style: 'ring', glareDisc: { cx: 40, cy: 32, rad: 7 } }); // ~154 of ~1414 mm2
    expect(codeOf(() => segmentClassic(rect))).toBe('GLARE');
  });

  it('a small saturated spot (under 5 %) is accepted', () => {
    const { rect, truth } = render({ shape: lens, style: 'ring', glareDisc: { cx: 40, cy: 32, rad: 2 } });
    expect(iou(segmentClassic(rect).data, truth)).toBeGreaterThanOrEqual(0.98);
  });

  it('only OptiError escapes: an inconsistent image is LOAD_FAILED', () => {
    const { rect } = render({ shape: lens, style: 'ring' });
    expect(codeOf(() => segmentClassic({ ...rect, pxPerMm: 0 }))).toBe('LOAD_FAILED');
  });
});

describe('segmentClassic, speed', () => {
  it('runs in under 300 ms on 800x650', () => {
    const { rect } = render({ shape: lens, style: 'ring' });
    segmentClassic(rect); // warm-up (JIT)
    const times: number[] = [];
    for (let i = 0; i < 3; i++) {
      const t0 = performance.now();
      segmentClassic(rect);
      times.push(performance.now() - t0);
    }
    expect(Math.min(...times)).toBeLessThan(300);
  });
});
