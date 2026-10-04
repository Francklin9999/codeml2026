import { OptiError, type BoardSpec, type ErrorCode, type Eye, type LensMeasurement, type Mask, type Photo, type Pt, type Rectified } from './contracts';
import { rectify } from './vision/rectify';
import { applyH } from './vision/homography';
import { segmentClassic } from './vision/segmentClassic';
import { measureLens, setBias } from './measure';
import type { Bias } from './measure/correction';

// Heavy work runs here so the UI thread stays responsive. Add new message
// types to WorkerRequest / WorkerResponse and a case in handleMessage.
//
// 'measure' returns the measurement only. 'debug' also returns the intermediate images for the
// step-by-step screen (one run, so the screens never measure the same photo twice).
export interface WorkerRequest { type: 'measure' | 'debug'; photo: Photo; spec: BoardSpec; eye: Eye; bias?: Bias }
/** What the "Pas à pas" screen shows. markers: sheet markers projected into photo pixels. */
export interface DebugSteps { markers: Pt[][]; rectified: Rectified['image']; mask: Mask }
export type WorkerResponse =
  | { ok: true; result: LensMeasurement; debug?: DebugSteps }
  | { ok: false; code: ErrorCode };
/** Progress: sent before each step. The sheet is located and the image rectified by one call, so they share a step. */
export type Step = 'locate' | 'isolate' | 'measure';
/** Below this mask score the classic mask is doubtful and the model gets a try. Real-world value: TO MEASURE. */
export const LOW_MASK_SCORE = 0.3;

async function segment(r: Rectified): Promise<Mask> {
  let classic: Mask | undefined;
  let failure: unknown;
  try {
    classic = segmentClassic(r);
  } catch (e) {
    // Only "no lens" is worth a second opinion: glare or a lens past the edge would fool the model too.
    if (!(e instanceof OptiError && e.code === 'NO_LENS')) throw e;
    failure = e;
  }
  if (classic && classic.score >= LOW_MASK_SCORE) return classic;
  try {
    // Loaded on demand: the model is optional and heavy (onnxruntime).
    const model = await import('./vision/segmentModel');
    if (await model.isModelAvailable()) return await model.segmentModel(r);
  } catch (e) {
    if (!classic && e instanceof OptiError && e.code !== 'LOAD_FAILED') throw e;
  }
  if (classic) return classic;
  throw failure;
}

export async function handleMessage(msg: WorkerRequest, onStep: (s: Step) => void = () => {}): Promise<WorkerResponse> {
  try {
    if (msg?.type !== 'measure' && msg?.type !== 'debug') throw new OptiError('LOAD_FAILED', 'unknown message type');
    if (msg.bias) setBias(msg.bias);
    onStep('locate');
    const rectified = await rectify(msg.photo, msg.spec);
    onStep('isolate');
    const mask = await segment(rectified);
    onStep('measure');
    const result = measureLens(rectified, mask, msg.eye);
    if (msg.type === 'measure') return { ok: true, result };
    const ps = msg.spec.printScale;
    const markers = msg.spec.markers.map((m) => m.corners.map((c) => applyH(rectified.H, [c[0] * ps, c[1] * ps])));
    return { ok: true, result, debug: { markers, rectified: rectified.image, mask } };
  } catch (e) {
    return { ok: false, code: e instanceof OptiError ? e.code : 'LOAD_FAILED' };
  }
}

// Only wire the message loop inside a real worker, so tests can import handleMessage.
const scope = globalThis as unknown as {
  WorkerGlobalScope?: unknown;
  onmessage: ((e: MessageEvent<WorkerRequest>) => void) | null;
  postMessage(m: WorkerResponse | { step: Step }): void;
};
if (typeof scope.WorkerGlobalScope !== 'undefined' && globalThis instanceof (scope.WorkerGlobalScope as typeof Object)) {
  scope.onmessage = async (e) => scope.postMessage(await handleMessage(e.data, (step) => scope.postMessage({ step })));
}
