import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { OptiError, type Rectified } from '../contracts';
import {
  MASK_THRESHOLD, MEAN, MODEL_H, MODEL_W, STD,
  fillHoles, getLastTimings, isModelAvailable, largestComponent, postprocess, preprocess,
  resizeBilinear, segmentModel, setAssetBase, setSessionForTests, type ModelSession,
} from './segmentModel';

const W = 700, H = 500; // 70 x 50 mm at 10 px/mm

function rectified(w = W, h = H): Rectified {
  const image = new ImageData(w, h);
  return { image, pxPerMm: 10, H: [1, 0, 0, 0, 1, 0, 0, 0, 1], reprojErrMm: 0, sharpness: 100 };
}

/** Flat logits with +8 inside the model-grid rectangle, -8 elsewhere. */
function logitsRect(x0: number, y0: number, x1: number, y1: number, extra?: (x: number, y: number) => number | undefined): Float32Array {
  const l = new Float32Array(MODEL_W * MODEL_H);
  for (let y = 0; y < MODEL_H; y++) {
    for (let x = 0; x < MODEL_W; x++) {
      const inside = x >= x0 && x < x1 && y >= y0 && y < y1;
      l[y * MODEL_W + x] = extra?.(x, y) ?? (inside ? 8 : -8);
    }
  }
  return l;
}

const fake = (logits: Float32Array): ModelSession & { calls: { dims: readonly number[]; len: number }[] } => {
  const calls: { dims: readonly number[]; len: number }[] = [];
  return { calls, run: async (input, dims) => { calls.push({ dims, len: input.length }); return logits; } };
};

afterEach(() => {
  setSessionForTests(null);
  setAssetBase(null);
  vi.unstubAllGlobals();
});

describe('preprocess', () => {
  it('lays out planar RGB and normalises with mean/std on a 2-colour image', () => {
    const img = new ImageData(40, 30);
    for (let y = 0; y < 30; y++) {
      for (let x = 0; x < 40; x++) {
        const o = (y * 40 + x) * 4;
        const left = x < 20;
        img.data.set(left ? [255, 0, 0, 255] : [0, 0, 255, 255], o);
      }
    }
    const t = preprocess(img);
    const plane = MODEL_W * MODEL_H;
    expect(t.length).toBe(3 * plane);
    const at = (c: number, x: number, y: number) => t[c * plane + y * MODEL_W + x];
    // Pixels well inside each half (bilinear blends only around the seam).
    const norm = (v: number, c: number) => (v - MEAN[c]) / STD[c];
    for (const y of [5, 160, 300]) {
      expect(at(0, 10, y)).toBeCloseTo(norm(1, 0), 5);
      expect(at(1, 10, y)).toBeCloseTo(norm(0, 1), 5);
      expect(at(2, 10, y)).toBeCloseTo(norm(0, 2), 5);
      expect(at(0, 370, y)).toBeCloseTo(norm(0, 0), 5);
      expect(at(1, 370, y)).toBeCloseTo(norm(0, 1), 5);
      expect(at(2, 370, y)).toBeCloseTo(norm(1, 2), 5);
    }
  });

  it('uses (x, y) -> y * W + x inside each plane (H=320 rows, W=384 columns)', () => {
    const img = new ImageData(MODEL_W, MODEL_H); // same size: resize is the identity
    img.data.fill(255);
    const o = (7 * MODEL_W + 11) * 4; // x=11, y=7
    img.data[o] = 0; // R of that pixel only
    const t = preprocess(img);
    const plane = MODEL_W * MODEL_H;
    expect(t[0 * plane + 7 * MODEL_W + 11]).toBeCloseTo((0 - MEAN[0]) / STD[0], 5);
    expect(t[0 * plane + 11 * MODEL_W + 7]).toBeCloseTo((1 - MEAN[0]) / STD[0], 5);
    expect(t[1 * plane + 7 * MODEL_W + 11]).toBeCloseTo((1 - MEAN[1]) / STD[1], 5);
  });

  it('ignores alpha', () => {
    const a = new ImageData(8, 8), b = new ImageData(8, 8);
    a.data.fill(100);
    b.data.fill(100);
    for (let i = 3; i < b.data.length; i += 4) b.data[i] = 0;
    // Cheap element-wise comparison: vitest's deep equality on two 368,640-element
    // Float32Arrays takes several seconds and times the test out.
    const pa = preprocess(a), pb = preprocess(b);
    expect(pa.length).toBe(pb.length);
    let firstDiff = -1;
    for (let i = 0; i < pa.length; i++) {
      if (pa[i] !== pb[i]) { firstDiff = i; break; }
    }
    expect(firstDiff).toBe(-1);
  });
});

describe('resizeBilinear', () => {
  it('keeps a constant image constant and interpolates a ramp', () => {
    const flat = resizeBilinear(new Float32Array(4 * 4).fill(0.25), 4, 4, 1, 9, 7);
    expect(Math.max(...flat)).toBeCloseTo(0.25, 6);
    expect(Math.min(...flat)).toBeCloseTo(0.25, 6);
    const ramp = resizeBilinear([0, 1], 2, 1, 1, 4, 1); // half-pixel centres: 0, 0.25, 0.75, 1
    expect([...ramp]).toEqual([0, 0.25, 0.75, 1].map((v) => expect.closeTo(v, 6)));
  });
});

describe('largestComponent and fillHoles', () => {
  it('keeps only the biggest 4-connected blob', () => {
    const w = 10, h = 6;
    const m = new Uint8Array(w * h);
    for (let y = 1; y < 5; y++) for (let x = 1; x < 5; x++) m[y * w + x] = 1; // 16 px
    m[1 * w + 8] = 1; m[2 * w + 8] = 1; // 2 px
    m[5 * w + 6] = 1; // diagonal neighbour of nothing: 1 px
    m[4 * w + 5] = 1; m[5 * w + 5] = 1; // touches the big blob by an edge: part of it
    const out = largestComponent(m, w, h);
    expect(out[1 * w + 8]).toBe(0);
    expect(out[5 * w + 6]).toBe(1); // 4-adjacent to (5,5), which joined the big blob
    expect(out[2 * w + 2]).toBe(1);
    expect(out.reduce((a, b) => a + b, 0)).toBe(16 + 2 + 1);
    expect(largestComponent(new Uint8Array(12), 4, 3).every((v) => v === 0)).toBe(true);
  });

  it('does not join blobs that only touch diagonally', () => {
    const out = largestComponent(new Uint8Array([1, 0, 0, 1]), 2, 2); // two 1-px blobs on a diagonal
    expect(out.reduce((x, y) => x + y, 0)).toBe(1);
  });

  it('fills interior holes but not background connected to the border', () => {
    const w = 9, h = 9;
    const m = new Uint8Array(w * h);
    for (let y = 1; y < 8; y++) for (let x = 1; x < 8; x++) m[y * w + x] = 1;
    m[4 * w + 4] = 0; m[4 * w + 5] = 0; // interior hole
    for (let y = 1; y < 4; y++) m[y * w + 7] = 0; // notch open to the top-right: stays open
    m[1 * w + 6] = 0; m[0 * w + 7] = 0;
    const f = fillHoles(m, w, h);
    expect(f[4 * w + 4]).toBe(1);
    expect(f[4 * w + 5]).toBe(1);
    expect(f[2 * w + 7]).toBe(0);
    expect(f[0]).toBe(0);
  });
});

describe('postprocess', () => {
  it('thresholds at sigmoid 0.5, resizes to the rectified size and scores the mask', () => {
    // model-grid rectangle 96..288 x 80..240 -> pixels ~175..525 x 125..375 (35 x 25 mm = 875 mm2)
    const mask = postprocess(logitsRect(96, 80, 288, 240), W, H, 10);
    expect(mask.method).toBe('model');
    expect(mask.width).toBe(W);
    expect(mask.height).toBe(H);
    expect(mask.data.length).toBe(W * H);
    expect(mask.data[250 * W + 350]).toBe(1);
    expect(mask.data[10 * W + 10]).toBe(0);
    const area = mask.data.reduce((a, b) => a + b, 0);
    expect(area / 100).toBeGreaterThan(850);
    expect(area / 100).toBeLessThan(900);
    expect(mask.score).toBeGreaterThan(0.99); // sigmoid(8) = 0.99966
    expect(MASK_THRESHOLD).toBe(0.5);
  });

  it('drops a small second blob and fills a hole inside the lens', () => {
    const l = logitsRect(96, 80, 288, 240, (x, y) => {
      if (x >= 150 && x < 170 && y >= 120 && y < 140) return -8; // hole
      if (x >= 330 && x < 360 && y >= 20 && y < 50) return 8; // stray blob, far from the lens
      return undefined;
    });
    const mask = postprocess(l, W, H, 10);
    expect(mask.data[203 * W + 292]).toBe(1); // hole centre (model 160,130)
    expect(mask.data[55 * W + 629]).toBe(0); // stray blob centre (model 345,35)
  });

  it('score is the mean probability inside the mask', () => {
    const mask = postprocess(logitsRect(96, 80, 288, 240, (x, y) => (x >= 96 && x < 288 && y >= 80 && y < 240 ? 0.4054651 : -8)), W, H, 10); // sigmoid = 0.6
    expect(mask.score).toBeCloseTo(0.6, 3);
  });

  it('empty or too small -> NO_LENS', () => {
    expect(() => postprocess(new Float32Array(MODEL_W * MODEL_H).fill(-8), W, H, 10)).toThrowError(expect.objectContaining({ code: 'NO_LENS' }));
    expect(() => postprocess(logitsRect(100, 100, 120, 120), W, H, 10)).toThrowError(expect.objectContaining({ code: 'NO_LENS' }));
  });

  it('larger than 4000 mm2 -> NO_LENS', () => {
    expect(() => postprocess(logitsRect(10, 10, 374, 310), 900, 600, 10)) // 90 x 60 mm window, mask ~4800 mm2
      .toThrowError(expect.objectContaining({ code: 'NO_LENS' }));
  });

  it('mask touching the border -> LENS_OUT_OF_WINDOW', () => {
    expect(() => postprocess(logitsRect(0, 80, 200, 240), W, H, 10)).toThrowError(expect.objectContaining({ code: 'LENS_OUT_OF_WINDOW' }));
  });

  it('wrong output size -> LOAD_FAILED', () => {
    expect(() => postprocess(new Float32Array(10), W, H, 10)).toThrowError(expect.objectContaining({ code: 'LOAD_FAILED' }));
  });
});

describe('segmentModel with a fake session', () => {
  it('runs the model on a 1x3x320x384 tensor and fills getLastTimings', async () => {
    const s = fake(logitsRect(96, 80, 288, 240));
    setSessionForTests(s, 123);
    const mask = await segmentModel(rectified());
    expect(s.calls).toEqual([{ dims: [1, 3, 320, 384], len: 3 * 320 * 384 }]);
    expect(mask.method).toBe('model');
    const t = getLastTimings();
    expect(Object.keys(t).sort()).toEqual(['loadMs', 'postMs', 'preMs', 'runMs']);
    expect(t.loadMs).toBe(123);
    for (const v of Object.values(t)) expect(Number.isFinite(v) && v >= 0).toBe(true);
  });

  it('turns a session crash into LOAD_FAILED and keeps OptiError codes', async () => {
    setSessionForTests({ run: async () => { throw new Error('boom'); } });
    await expect(segmentModel(rectified())).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    setSessionForTests(fake(new Float32Array(MODEL_W * MODEL_H).fill(-8)));
    await expect(segmentModel(rectified())).rejects.toBeInstanceOf(OptiError);
    await expect(segmentModel(rectified())).rejects.toMatchObject({ code: 'NO_LENS' });
  });
});

describe('missing model', () => {
  const stubFetch = (impl: (...a: [string]) => Promise<Response>) => {
    const f = vi.fn<(...a: [string]) => Promise<Response>>(impl);
    vi.stubGlobal('fetch', f);
    return f;
  };

  it('404 -> isModelAvailable false, segmentModel throws LOAD_FAILED', async () => {
    const f = stubFetch(async () => new Response('nope', { status: 404 }));
    setAssetBase('http://localhost/app/');
    expect(await isModelAvailable()).toBe(false);
    expect(f.mock.calls[0][0]).toBe('http://localhost/app/models/lens_seg.onnx');
    await expect(segmentModel(rectified())).rejects.toMatchObject({ code: 'LOAD_FAILED' });
  });

  it('asks once, with a HEAD request: a site without a model never downloads the model or the runtime again', async () => {
    const f = vi.fn(async (_u: string, _init?: RequestInit) => new Response(null, { status: 404 }));
    vi.stubGlobal('fetch', f);
    setAssetBase('http://localhost/app/');
    expect(await isModelAvailable()).toBe(false);
    expect(await isModelAvailable()).toBe(false);
    await expect(segmentModel(rectified())).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    expect(f).toHaveBeenCalledTimes(1);
    expect(f.mock.calls[0][1]).toEqual({ method: 'HEAD' });
  });

  it('dev server answering index.html with 200 counts as missing', async () => {
    stubFetch(async () => new Response('<html></html>', { status: 200, headers: { 'content-type': 'text/html' } }));
    setAssetBase('http://localhost/');
    expect(await isModelAvailable()).toBe(false);
  });

  it('network failure -> false, no unhandled rejection, and a later call retries', async () => {
    const f = stubFetch(async () => { throw new TypeError('offline'); });
    setAssetBase('http://localhost/');
    expect(await isModelAvailable()).toBe(false);
    expect(await isModelAvailable()).toBe(false);
    expect(f).toHaveBeenCalledTimes(2);
  });
});

// End to end through the real onnxruntime-web WASM runtime (single thread) with a 160-byte stand-in
// model: logits = 4 * normalised R - 0.065, so a red shape on black is the "lens". Not lens_seg.onnx.
const TINY_MODEL_B64 =
  'CAg6lQEKGwoFaW5wdXQKAXcKAWISBmxvZ2l0cyIEQ29udhIDc2VnKhsIAQgDCAEIARABQgF3SgwAAIBAAAAAAAAAAAAqDQgBEAFCAWJKBLgehb1aIQoFaW5wdXQSGAoWCAESEgoCCAEKAggDCgMIwAIKAwiAA2IiCgZsb2dpdHMSGAoWCAESEgoCCAEKAggBCgMIwAIKAwiAA0IECgAQDQ==';
const vendorDir = resolve(import.meta.dirname, '../../public/vendor/ort');

describe.skipIf(!existsSync(resolve(vendorDir, 'ort-wasm-simd-threaded.wasm')))('real onnxruntime-web WASM session', () => {
  it('loads a model by its fixed URL, runs it and returns a lens mask', async () => {
    const urls: string[] = [];
    vi.stubGlobal('fetch', async (u: string, init?: RequestInit) => {
      if (init?.method !== 'HEAD') urls.push(u); // the HEAD probe comes first; only downloads are counted
      return new Response(Buffer.from(TINY_MODEL_B64, 'base64'), { status: 200, headers: { 'content-type': 'application/octet-stream' } });
    });
    setAssetBase(pathToFileURL(resolve(import.meta.dirname, '../../public') + '/').href);
    expect(await isModelAvailable()).toBe(true);
    expect(urls).toHaveLength(1);
    expect(urls[0].endsWith('/models/lens_seg.onnx')).toBe(true);

    const r = rectified();
    for (let y = 150; y < 400; y++) for (let x = 200; x < 550; x++) r.image.data.set([255, 0, 0, 255], (y * W + x) * 4);
    const mask = await segmentModel(r);
    expect(mask.data[250 * W + 350]).toBe(1);
    expect(mask.data[20 * W + 20]).toBe(0);
    const area = mask.data.reduce((a, b) => a + b, 0) / 100;
    expect(area).toBeGreaterThan(800);
    expect(area).toBeLessThan(950);
    expect(urls).toHaveLength(1); // session reused, model not fetched again
    await segmentModel(r);
    expect(urls).toHaveLength(1);
    expect(getLastTimings().runMs).toBeGreaterThan(0);
  }, 60_000);
});
