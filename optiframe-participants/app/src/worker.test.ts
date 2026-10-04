import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OptiError, type BoardSpec, type Photo } from './contracts';

// The module stubs of brief 01 throw LOAD_FAILED; later briefs replace them, so the test
// pins that behaviour with mocks instead of depending on the real modules.
const rectify = vi.hoisted(() => vi.fn());
const segmentClassic = vi.hoisted(() => vi.fn());
const measureLens = vi.hoisted(() => vi.fn());
const setBias = vi.hoisted(() => vi.fn());
const isModelAvailable = vi.hoisted(() => vi.fn());
const segmentModel = vi.hoisted(() => vi.fn());
vi.mock('./vision/rectify', () => ({ rectify }));
vi.mock('./vision/segmentClassic', () => ({ segmentClassic }));
vi.mock('./vision/segmentModel', () => ({ isModelAvailable, segmentModel }));
vi.mock('./measure', () => ({ measureLens, setBias }));

import { handleMessage, ownBuffers, type WorkerRequest } from './worker';

const photo: Photo = { image: new ImageData(2, 2), source: 'file' };
const spec = {} as BoardSpec;
const request: WorkerRequest = { type: 'measure', photo, spec, eye: 'R' };

describe('worker pipeline', () => {
  beforeEach(() => {
    rectify.mockReset();
    segmentClassic.mockReset();
    measureLens.mockReset();
    setBias.mockReset();
    isModelAvailable.mockReset().mockResolvedValue(false);
    segmentModel.mockReset();
  });

  it('answers LOAD_FAILED when the modules are stubs', async () => {
    rectify.mockRejectedValue(new OptiError('LOAD_FAILED', 'not implemented'));
    expect(await handleMessage(request)).toEqual({ ok: false, code: 'LOAD_FAILED' });
  });

  it('keeps the error code of the failing step', async () => {
    rectify.mockResolvedValue({});
    segmentClassic.mockImplementation(() => {
      throw new OptiError('NO_LENS');
    });
    expect(await handleMessage(request)).toEqual({ ok: false, code: 'NO_LENS' });
  });

  it('maps unexpected exceptions to LOAD_FAILED', async () => {
    rectify.mockRejectedValue(new TypeError('boom'));
    expect(await handleMessage(request)).toEqual({ ok: false, code: 'LOAD_FAILED' });
  });

  it('chains rectify, segmentClassic, measureLens', async () => {
    const rectified = { tag: 'r' };
    const mask = { tag: 'm' };
    const result = { tag: 'result' };
    rectify.mockResolvedValue(rectified);
    segmentClassic.mockReturnValue(mask);
    measureLens.mockReturnValue(result);
    expect(await handleMessage(request)).toEqual({ ok: true, result, timings: expect.any(Object) });
    expect(rectify).toHaveBeenCalledWith(photo, spec);
    expect(segmentClassic).toHaveBeenCalledWith(rectified);
    expect(measureLens).toHaveBeenCalledWith(rectified, mask, 'R');
  });

  it('rejects an unknown message type', async () => {
    const bad = { type: 'nope' } as unknown as WorkerRequest;
    expect(await handleMessage(bad)).toEqual({ ok: false, code: 'LOAD_FAILED' });
  });
  it('sets the bias before measuring, when the message carries one', async () => {
    const bias = { a0: 0.1, a1: 1, b0: 0, b1: 1 };
    rectify.mockResolvedValue({});
    segmentClassic.mockReturnValue({ score: 1 });
    measureLens.mockImplementation(() => {
      expect(setBias).toHaveBeenCalledWith(bias);
      return { tag: 'r' };
    });
    expect(await handleMessage({ ...request, bias })).toEqual({ ok: true, result: { tag: 'r' }, timings: expect.any(Object) });
  });

  it('reports the steps in order', async () => {
    rectify.mockResolvedValue({});
    segmentClassic.mockReturnValue({ score: 1 });
    measureLens.mockReturnValue({});
    const steps: string[] = [];
    await handleMessage(request, (s) => steps.push(s));
    expect(steps).toEqual(['locate', 'isolate', 'measure']);
  });

  it('falls back to the model on NO_LENS when it is available', async () => {
    const modelMask = { tag: 'model', score: 0.9 };
    rectify.mockResolvedValue({});
    segmentClassic.mockImplementation(() => { throw new OptiError('NO_LENS'); });
    isModelAvailable.mockResolvedValue(true);
    segmentModel.mockResolvedValue(modelMask);
    measureLens.mockReturnValue({ tag: 'result' });
    expect(await handleMessage(request)).toEqual({ ok: true, result: { tag: 'result' }, timings: expect.any(Object) });
    expect(measureLens).toHaveBeenCalledWith({}, modelMask, 'R');
  });

  it('keeps NO_LENS when the model is not available, or fails to load', async () => {
    rectify.mockResolvedValue({});
    segmentClassic.mockImplementation(() => { throw new OptiError('NO_LENS'); });
    expect(await handleMessage(request)).toEqual({ ok: false, code: 'NO_LENS' });
    isModelAvailable.mockResolvedValue(true);
    segmentModel.mockRejectedValue(new OptiError('LOAD_FAILED'));
    expect(await handleMessage(request)).toEqual({ ok: false, code: 'NO_LENS' });
  });

  it('does not ask the model about glare', async () => {
    rectify.mockResolvedValue({});
    segmentClassic.mockImplementation(() => { throw new OptiError('GLARE'); });
    isModelAvailable.mockResolvedValue(true);
    expect(await handleMessage(request)).toEqual({ ok: false, code: 'GLARE' });
    expect(segmentModel).not.toHaveBeenCalled();
  });

  it('tries the model on a low classic score, and keeps the classic mask if the model is missing', async () => {
    const weak = { tag: 'classic', score: 0.1 };
    rectify.mockResolvedValue({});
    segmentClassic.mockReturnValue(weak);
    measureLens.mockReturnValue({ tag: 'result' });
    await handleMessage(request);
    expect(measureLens).toHaveBeenLastCalledWith({}, weak, 'R');
    const strong = { tag: 'model', score: 0.8 };
    isModelAvailable.mockResolvedValue(true);
    segmentModel.mockResolvedValue(strong);
    await handleMessage(request);
    expect(measureLens).toHaveBeenLastCalledWith({}, strong, 'R');
  });

  it('times every stage, beside the measurement', async () => {
    rectify.mockResolvedValue({});
    segmentClassic.mockReturnValue({ score: 1 });
    measureLens.mockReturnValue({});
    const res = await handleMessage(request);
    if (!res.ok) throw new Error(res.code);
    for (const k of ['rectify', 'segment', 'measure', 'worker']) expect(res.timings[k], k).toBeGreaterThanOrEqual(0);
    expect(res.timings.worker).toBeGreaterThanOrEqual(res.timings.rectify);
  });

  it('transfers each pixel buffer once, and never a slice of a larger buffer', () => {
    const a = new Uint8ClampedArray(16), b = new Uint8Array(8);
    const heap = new Uint8Array(new ArrayBuffer(64), 8, 16); // like a view into WASM memory
    expect(ownBuffers(a, b, a, heap, undefined, new Uint8Array(0))).toEqual([a.buffer, b.buffer]);
  });

  it('debug returns the images and the projected markers', async () => {
    const rectified = { H: [1, 0, 5, 0, 1, 7, 0, 0, 1], image: { tag: 'img' } };
    const mask = { score: 1 };
    rectify.mockResolvedValue(rectified);
    segmentClassic.mockReturnValue(mask);
    measureLens.mockReturnValue({ tag: 'result' });
    const spec = { printScale: 2, markers: [{ id: 0, corners: [[0, 0], [1, 0], [1, 1], [0, 1]] }] } as unknown as BoardSpec;
    const res = await handleMessage({ ...request, type: 'debug', spec });
    expect(res).toEqual({ ok: true, result: { tag: 'result' }, timings: expect.any(Object), debug: { markers: [[[5, 7], [7, 7], [7, 9], [5, 9]]], rectified: rectified.image, mask } });
  });
});
