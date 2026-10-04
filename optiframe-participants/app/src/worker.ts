import { OptiError, type BoardSpec, type ErrorCode, type Eye, type LensMeasurement, type Mask, type Photo, type Pt, type Rectified } from './contracts';
import { locateReference, rectify } from './vision/rectify';
import { applyH } from './vision/homography';
import { loadOpenCv } from './vision/opencv';
import { segmentClassic } from './vision/segmentClassic';
import { measureLens, setBias } from './measure';
import type { Bias } from './measure/correction';
import { now, resetTimings, takeTimings, timed, timedAsync, type Timings } from './timing';

// Heavy work runs here so the UI thread stays responsive. Add new message
// types to WorkerRequest / WorkerResponse and a case in handleMessage.
//
// 'measure' returns the measurement only. 'debug' also returns the intermediate images for the
// step-by-step screen (one run, so the screens never measure the same photo twice).
export interface WorkerRequest { type: 'measure' | 'debug'; photo: Photo; spec: BoardSpec; eye: Eye; bias?: Bias }
/** What the "Pas à pas" screen shows. markers: sheet markers projected into photo pixels. */
export interface DebugSteps { markers: Pt[][]; rectified: Rectified['image']; mask: Mask }
/** timings: milliseconds per stage of this photo (see STAGE order in ui/screens.ts), beside the measurement. */
export type WorkerResponse =
  | { ok: true; result: LensMeasurement; timings: Timings; debug?: DebugSteps }
  | { ok: false; code: ErrorCode };
/** Sheet check of the data-collection page: same rectify as a measurement, no lens needed. */
export interface CheckRequest { type: 'check'; photo: Photo; spec: BoardSpec }
export type CheckResponse = { ok: true; nMarkers?: number } | { ok: false; code: ErrorCode };
/** OpenCV.js in the worker: fetched and compiled in the background from the home screen on. */
export type EngineState = 'idle' | 'loading' | 'ready' | 'failed';
/** What crosses the worker boundary. Pixel buffers are transferred (moved), never copied: see ownBuffers. */
export type WireIn = WorkerRequest | CheckRequest | { type: 'warmup' };
export type WireOut =
  | { step: Step }
  | { engine: EngineState }
  | { done: WorkerResponse | CheckResponse; image?: ImageData }; // image: the photo, handed back to the page
/** Progress: sent before each step. The sheet is located and the image rectified by one call, so they share a step. */
export type Step = 'locate' | 'isolate' | 'measure';
/** Below this mask score the classic mask is doubtful and the model gets a try. Real-world value: TO MEASURE. */
export const LOW_MASK_SCORE = 0.3;

/**
 * Transfer list for postMessage: the buffers of the views that own their whole buffer. A view into a larger buffer
 * (WASM memory) is left out and structured-cloned instead. Each buffer once: a duplicate makes postMessage throw.
 */
export function ownBuffers(...views: (ArrayBufferView | null | undefined)[]): ArrayBuffer[] {
  const out = new Set<ArrayBuffer>();
  for (const v of views) {
    if (v && v.buffer instanceof ArrayBuffer && v.byteOffset === 0 && v.byteLength === v.buffer.byteLength && v.byteLength > 0) out.add(v.buffer);
  }
  return [...out];
}

async function segment(r: Rectified): Promise<Mask> {
  let classic: Mask | undefined;
  let failure: unknown;
  try {
    classic = segmentClassic(r);
  } catch (e) {
    // "No lens" and "lens past the border" get a second opinion: a dark speckle or strip at the border can read as a
    // lens past it, and the model refuses a mask that comes near the border itself (postprocess), so a lens really past
    // the border is still refused. Glare would fool the model too: it stays final.
    if (!(e instanceof OptiError && (e.code === 'NO_LENS' || e.code === 'LENS_OUT_OF_WINDOW'))) throw e;
    failure = e;
  }
  if (classic && classic.score >= LOW_MASK_SCORE) return classic;
  try {
    // Loaded on demand: the model is optional and heavy (onnxruntime).
    const model = await import('./vision/segmentModel');
    if (await model.isModelAvailable()) return await model.segmentModel(r);
  } catch (e) {
    if (!classic && e instanceof OptiError && e.code !== 'LOAD_FAILED') {
      // The classic "past the border" stands unless the model measured a lens inside the window.
      throw failure instanceof OptiError && failure.code === 'LENS_OUT_OF_WINDOW' ? failure : e;
    }
  }
  if (classic) return classic;
  throw failure;
}

export async function handleMessage(msg: WorkerRequest, onStep: (s: Step) => void = () => {}): Promise<WorkerResponse> {
  try {
    if (msg?.type !== 'measure' && msg?.type !== 'debug') throw new OptiError('LOAD_FAILED', 'unknown message type');
    if (msg.bias) setBias(msg.bias);
    resetTimings();
    const t0 = now();
    onStep('locate');
    const rectified = await timedAsync('rectify', () => rectify(msg.photo, msg.spec));
    onStep('isolate');
    const mask = await timedAsync('segment', () => segment(rectified));
    onStep('measure');
    const result = timed('measure', () => measureLens(rectified, mask, msg.eye));
    const timings = { ...takeTimings(), worker: now() - t0 };
    if (msg.type === 'measure') return { ok: true, result, timings };
    const ps = msg.spec.printScale;
    const markers = msg.spec.markers.map((m) => m.corners.map((c) => applyH(rectified.H, [c[0] * ps, c[1] * ps])));
    return { ok: true, result, timings, debug: { markers, rectified: rectified.image, mask } };
  } catch (e) {
    return { ok: false, code: e instanceof OptiError ? e.code : 'LOAD_FAILED' };
  }
}

/**
 * Loads the optional model in the background once OpenCV is ready, so the first photo that needs it does not wait
 * for its download (model about 8 MB + onnxruntime 14 MB). Without a deployed model this is one HEAD request.
 * Skipped when the browser asks to save data. Resolves with whether the model is ready; never rejects.
 */
export async function prefetchModel(nav: { connection?: { saveData?: boolean } } | undefined = (globalThis as { navigator?: { connection?: { saveData?: boolean } } }).navigator): Promise<boolean> {
  if (nav?.connection?.saveData) return false;
  try {
    const model = await import('./vision/segmentModel');
    return await model.isModelAvailable();
  } catch {
    return false;
  }
}

/** Is the sheet readable in this photo? Resolves with the marker count when it can be read. */
export async function handleCheck(msg: CheckRequest): Promise<CheckResponse> {
  try {
    await rectify(msg.photo, msg.spec);
    // rectify returns no marker count; locateReference is what it calls first.
    let nMarkers: number | undefined;
    try { nMarkers = (await locateReference(msg.photo, msg.spec)).nMarkers; } catch { /* count is optional */ }
    return { ok: true, nMarkers };
  } catch (e) {
    return { ok: false, code: e instanceof OptiError ? e.code : 'LOAD_FAILED' };
  }
}

// Only wire the message loop inside a real worker, so tests can import handleMessage.
const scope = globalThis as unknown as {
  WorkerGlobalScope?: unknown;
  onmessage: ((e: MessageEvent<WireIn>) => void) | null;
  postMessage(m: WireOut, transfer?: Transferable[]): void;
};
if (typeof scope.WorkerGlobalScope !== 'undefined' && globalThis instanceof (scope.WorkerGlobalScope as typeof Object)) {
  scope.onmessage = async (e) => {
    const msg = e.data;
    if (msg?.type === 'warmup') {
      // The 13 MB of OpenCV.js are fetched and compiled here, off the UI thread; photos share the same promise.
      loadOpenCv().then(() => { scope.postMessage({ engine: 'ready' }); void prefetchModel(); }, () => scope.postMessage({ engine: 'failed' }));
      return;
    }
    const image = msg?.photo?.image;
    const done = msg?.type === 'check' ? await handleCheck(msg) : await handleMessage(msg, (step) => scope.postMessage({ step }));
    const debug = 'debug' in done ? done.debug : undefined;
    const out: WireOut = image ? { done, image } : { done };
    try {
      // The photo goes back to the page and the step images follow it: buffers are moved, nothing is copied.
      scope.postMessage(out, ownBuffers(image?.data, debug?.rectified.data, debug?.mask.data));
    } catch {
      scope.postMessage(out); // a buffer that cannot be transferred is cloned instead
    }
  };
}
