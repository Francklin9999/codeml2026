import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OptiError, type BoardSpec, type ErrorCode, type Photo } from '../contracts';

// Mocked modules behind the real pipeline.ts and the real worker.ts (no Worker in Node: the pipeline runs handleMessage inline).
const rectify = vi.hoisted(() => vi.fn());
const segmentClassic = vi.hoisted(() => vi.fn());
const measureLens = vi.hoisted(() => vi.fn());
const setBias = vi.hoisted(() => vi.fn());
const isModelAvailable = vi.hoisted(() => vi.fn());
const segmentModel = vi.hoisted(() => vi.fn());
vi.mock('../vision/rectify', () => ({ rectify }));
vi.mock('../vision/segmentClassic', () => ({ segmentClassic }));
vi.mock('../vision/segmentModel', () => ({ isModelAvailable, segmentModel }));
vi.mock('../measure', () => ({ measureLens, setBias, rotationWarningDeg: () => null }));

import { finishLens, loadAssets, measureOne, measureOneDebug, setAssets, setProgressListener, setRunner } from '../pipeline';
import { messageFor } from '../quality';

const ALL_CODES: ErrorCode[] = ['NO_REFERENCE', 'REFERENCE_TILTED', 'BLURRY', 'NO_LENS', 'LENS_OUT_OF_WINDOW', 'GLARE', 'INCONSISTENT_SHOTS', 'LENS_ROTATED', 'CAMERA_DENIED', 'LOAD_FAILED'];
const photo: Photo = { image: new ImageData(2, 2), source: 'file' };
const spec = { printScale: 1, markers: [], windowMm: { w: 80, h: 65 } } as unknown as BoardSpec;
const bias = { a0: 0, a1: 1, b0: 0, b1: 1 };
const lens = { eye: 'R', A: 50, B: 40 };

beforeEach(() => {
  for (const f of [rectify, segmentClassic, measureLens, setBias, isModelAvailable, segmentModel]) f.mockReset();
  isModelAvailable.mockResolvedValue(false);
  rectify.mockResolvedValue({ H: [1, 0, 0, 0, 1, 0, 0, 0, 1], image: new ImageData(2, 2) });
  setAssets({ spec, bias });
  setRunner(null);
  setProgressListener(null);
});
afterEach(() => { setAssets(null); setRunner(null); vi.unstubAllGlobals(); });

describe('measureOne', () => {
  it('returns the measurement and passes the sheet and the bias to the worker', async () => {
    segmentClassic.mockReturnValue({ score: 1, method: 'classic' });
    measureLens.mockReturnValue(lens);
    expect(await measureOne(photo, 'R')).toBe(lens);
    expect(rectify).toHaveBeenCalledWith(photo, spec);
    expect(setBias).toHaveBeenCalledWith(bias);
  });

  it('falls back to the model on NO_LENS when it is available', async () => {
    const mask = { score: 0.9, method: 'model' };
    segmentClassic.mockImplementation(() => { throw new OptiError('NO_LENS'); });
    isModelAvailable.mockResolvedValue(true);
    segmentModel.mockResolvedValue(mask);
    measureLens.mockReturnValue(lens);
    expect(await measureOne(photo, 'R')).toBe(lens);
    expect(measureLens.mock.calls[0][1]).toBe(mask);
  });

  it('keeps NO_LENS (and its message) when the model is not available', async () => {
    segmentClassic.mockImplementation(() => { throw new OptiError('NO_LENS'); });
    const err = await measureOne(photo, 'R').catch((e) => e);
    expect(err).toBeInstanceOf(OptiError);
    expect(err.code).toBe('NO_LENS');
    expect(messageFor(err.code)).toContain('verre');
    expect(segmentModel).not.toHaveBeenCalled();
  });

  for (const code of ALL_CODES) {
    it(`${code} comes out as an OptiError with that code`, async () => {
      rectify.mockRejectedValue(new OptiError(code, 'internal detail'));
      const err = await measureOne(photo, 'L').catch((e) => e);
      expect(err).toBeInstanceOf(OptiError);
      expect(err.code).toBe(code);
    });
  }

  it.each([
    ['an Error', () => new Error('boom')],
    ['a TypeError', () => new TypeError('x is undefined')],
    ['a thrown string', () => 'oops'],
    ['undefined', () => undefined],
  ])('%s maps to LOAD_FAILED', async (_n, make) => {
    rectify.mockImplementation(async () => { throw make(); });
    const err = await measureOne(photo, 'R').catch((e) => e);
    expect(err).toBeInstanceOf(OptiError);
    expect(err.code).toBe('LOAD_FAILED');
  });

  it('a runner that throws, or answers garbage, maps to LOAD_FAILED', async () => {
    setRunner(async () => { throw new RangeError('x'); });
    expect((await measureOne(photo, 'R').catch((e) => e)).code).toBe('LOAD_FAILED');
    setRunner((async () => ({ ok: false })) as never);
    const err = await measureOne(photo, 'R').catch((e) => e);
    expect(err).toBeInstanceOf(OptiError);
  });

  it('missing static files (no document in Node) is LOAD_FAILED, and a later call retries', async () => {
    setAssets(null);
    expect((await measureOne(photo, 'R').catch((e) => e)).code).toBe('LOAD_FAILED');
    const fetched: string[] = [];
    vi.stubGlobal('document', { baseURI: 'https://example.test/app/' });
    vi.stubGlobal('fetch', async (u: URL) => {
      fetched.push(String(u));
      return { ok: true, json: async () => (String(u).endsWith('bias.json') ? bias : spec) };
    });
    await expect(loadAssets()).resolves.toEqual({ spec, bias });
    expect(fetched.sort()).toEqual(['https://example.test/app/bias.json', 'https://example.test/app/board_spec.json']);
  });

  it('a 404 on board_spec.json is LOAD_FAILED', async () => {
    setAssets(null);
    vi.stubGlobal('document', { baseURI: 'https://example.test/' });
    vi.stubGlobal('fetch', async () => ({ ok: false, status: 404, json: async () => ({}) }));
    expect((await loadAssets().catch((e) => e)).code).toBe('LOAD_FAILED');
  });

  it('names the steps through the progress listener', async () => {
    segmentClassic.mockReturnValue({ score: 1 });
    measureLens.mockReturnValue(lens);
    const seen: string[] = [];
    setProgressListener((s) => seen.push(s));
    await measureOne(photo, 'R');
    expect(seen).toEqual(['locate', 'isolate', 'measure']);
  });

  it('runs two photos one after the other', async () => {
    const order: string[] = [];
    setRunner(async (req) => { order.push('start'); await new Promise((r) => setTimeout(r, 5)); order.push('end'); return { ok: true, result: lens as never }; });
    await Promise.all([measureOne(photo, 'R'), measureOne(photo, 'R')]);
    expect(order).toEqual(['start', 'end', 'start', 'end']);
  });
});

describe('measureOneDebug and finishLens', () => {
  it('gives the images of the step-by-step screen', async () => {
    segmentClassic.mockReturnValue({ score: 1, method: 'classic', data: new Uint8Array(4), width: 2, height: 2 });
    measureLens.mockReturnValue(lens);
    const { result, steps } = await measureOneDebug(photo, 'R');
    expect(result).toBe(lens);
    expect(steps.rectified.width).toBe(2);
    expect(steps.mask.width).toBe(2);
  });

  it('finishLens throws an OptiError only', () => {
    expect(() => finishLens([])).toThrow(OptiError);
    expect(() => finishLens(null as never)).toThrow(OptiError);
  });
});
