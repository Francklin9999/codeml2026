// Pipeline between the screens and the heavy modules. Public API (briefs 14 and 17 import it):
//
//   measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement>
//       one photo of one lens: rectify -> segment (classic, model as fallback) -> measure.
//       Resolves with the measurement; rejects with an OptiError only (any other failure becomes LOAD_FAILED).
//   measureOneDebug(photo, eye): Promise<{ result: LensMeasurement; steps: DebugSteps; timings: Timings }>
//       same run, plus the images of the step-by-step screen and the duration of every stage (ms).
//   checkSheet(photo): Promise<{ nMarkers?: number }>
//       is the sheet readable in this photo (no lens needed); rejects with an OptiError.
//   warmUp(), setEngineListener(cb), engineState()
//       OpenCV.js (13 MB) is fetched and compiled inside the worker only; warmUp starts that in the background.
//   finishLens(shots: LensMeasurement[]): LensMeasurement
//       fuses 1 to 3 shots of the same lens (fuseShots); rejects with an OptiError.
//
// board_spec.json and bias.json are fetched once from public/. The work runs in a Web Worker; where there is
// none (tests, very old browsers) it runs on the calling thread through the same handleMessage.
// Photos go to the worker and come back as transferables: the pixel buffer is moved, not copied, so photo.image is
// empty while the photo is being measured and is put back when the answer arrives.
import { OptiError, type BoardSpec, type Eye, type LensMeasurement, type Photo } from './contracts';
import type { Bias } from './measure/correction';
import { fuseShots } from './quality';
import type { Timings } from './timing';
import type { CheckRequest, CheckResponse, DebugSteps, EngineState, Step, WireOut, WorkerRequest, WorkerResponse } from './worker';

export type { DebugSteps, EngineState, Step } from './worker';
export type { Timings } from './timing';

export const STEP_LABELS: Record<Step, string> = {
  locate: "Je repère la feuille et je redresse l'image",
  isolate: "J'isole le verre",
  measure: 'Je mesure',
};
export interface Assets { spec: BoardSpec; bias: Bias }
export type Runner = (req: WorkerRequest, onStep: (s: Step) => void) => Promise<WorkerResponse>;

/** Any failure becomes an OptiError: no other exception type reaches the screens. */
export function toOptiError(e: unknown): OptiError {
  return e instanceof OptiError ? e : new OptiError('LOAD_FAILED');
}

const now = (): number => performance.now();

let assets: Promise<Assets> | undefined;
let runner: Runner | undefined;
let progress: ((s: Step) => void) | undefined;
let queue: Promise<unknown> = Promise.resolve();

/** Tests: replace the worker, or the static files (null restores the default). */
export function setRunner(r: Runner | null): void { runner = r ?? undefined; }
export function setAssets(a: Assets | null): void { assets = a ? Promise.resolve(a) : undefined; }
/** The screens listen here to name the current step. */
export function setProgressListener(cb: ((s: Step) => void) | null): void { progress = cb ?? undefined; }

async function fetchJson(name: string): Promise<unknown> {
  const res = await fetch(new URL(name, document.baseURI));
  if (!res.ok) throw new OptiError('LOAD_FAILED', `${name}: ${res.status}`);
  return res.json();
}

export function loadAssets(): Promise<Assets> {
  assets ??= (async () => {
    try {
      const [spec, bias] = (await Promise.all([fetchJson('board_spec.json'), fetchJson('bias.json')])) as [BoardSpec, Bias];
      if (!Array.isArray(spec?.markers) || !spec.windowMm || !Number.isFinite(spec.printScale)) throw new OptiError('LOAD_FAILED', 'board_spec.json');
      return { spec, bias };
    } catch (e) {
      throw toOptiError(e);
    }
  })();
  assets.catch(() => { assets = undefined; }); // a later call retries
  return assets;
}

let worker: Worker | undefined;
/** The one job the worker is busy with (pipeline.ts queues the photos). */
let job: { photo: Photo; onStep(s: Step): void; resolve(r: WorkerResponse | CheckResponse): void } | undefined;
let engine: EngineState = 'idle';
let engineListener: ((s: EngineState) => void) | undefined;

function setEngine(s: EngineState): void {
  if (s === engine) return;
  engine = s;
  engineListener?.(s);
}
export function engineState(): EngineState { return engine; }
/** The screens listen here to say that the measuring tool is still loading. Called at once with the current state. */
export function setEngineListener(cb: ((s: EngineState) => void) | null): void {
  engineListener = cb ?? undefined;
  cb?.(engine);
}

const hasWorker = (): boolean => !runner && typeof Worker !== 'undefined';

function getWorker(): Worker {
  if (worker) return worker;
  const w = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });
  w.onmessage = (e: MessageEvent<WireOut>) => {
    const m = e.data;
    if ('step' in m) { job?.onStep(m.step); return; }
    if ('engine' in m) { setEngine(m.engine); return; }
    const j = job;
    job = undefined;
    if (!j) return;
    if (m.image) j.photo.image = m.image; // the pixels come back with the answer
    // Any answer other than a failed load proves that OpenCV is up.
    if (m.done.ok || m.done.code !== 'LOAD_FAILED') setEngine('ready');
    j.resolve(m.done);
  };
  w.onerror = () => {
    w.terminate();
    worker = undefined;
    setEngine(engine === 'loading' ? 'failed' : 'idle'); // a new worker loads OpenCV again
    const j = job;
    job = undefined;
    j?.resolve({ ok: false, code: 'LOAD_FAILED' });
  };
  worker = w;
  return w;
}

/**
 * Starts loading OpenCV.js inside the worker, in the background. Call it when the home screen is shown.
 * Without a Worker (tests, very old browsers) there is nothing to prepare off the UI thread: OpenCV then loads with the first photo.
 */
export function warmUp(): void {
  if (engine === 'loading' || engine === 'ready') return;
  if (!hasWorker()) { setEngine('ready'); return; }
  setEngine('loading');
  try {
    getWorker().postMessage({ type: 'warmup' });
  } catch {
    setEngine('failed');
  }
}

function post<R extends WorkerResponse | CheckResponse>(req: WorkerRequest | CheckRequest, onStep: (s: Step) => void): Promise<R> {
  const w = getWorker();
  return new Promise<R>((resolve) => {
    job = { photo: req.photo, onStep, resolve: resolve as (r: WorkerResponse | CheckResponse) => void };
    const data = req.photo.image.data;
    // Moved, not copied. Guarded like ownBuffers in worker.ts (not imported: worker.ts must stay out of the page bundle).
    const own = data.buffer instanceof ArrayBuffer && data.byteOffset === 0 && data.byteLength === data.buffer.byteLength && data.byteLength > 0;
    try {
      w.postMessage(req, own ? [data.buffer] : []);
    } catch {
      job = undefined;
      resolve({ ok: false, code: 'LOAD_FAILED' } as R);
    }
  });
}

const defaultRunner: Runner = async (req, onStep) => {
  if (typeof Worker === 'undefined') {
    const { handleMessage } = await import('./worker');
    return handleMessage(req, onStep);
  }
  return post<WorkerResponse>(req, onStep);
};

/** One photo at a time: the worker has one reply slot. Rejects with an OptiError only. */
function enqueue<T>(work: (a: Assets) => Promise<T>): Promise<T> {
  const task = queue.then(async () => {
    try {
      return await work(await loadAssets());
    } catch (e) {
      throw toOptiError(e);
    }
  });
  queue = task.catch(() => {});
  return task;
}

function run(type: 'measure' | 'debug', photo: Photo, eye: Eye): Promise<Extract<WorkerResponse, { ok: true }>> {
  return enqueue(async ({ spec, bias }) => {
    const t0 = now();
    const res = await (runner ?? defaultRunner)({ type, photo, spec, eye, bias }, (s) => progress?.(s));
    if (!res.ok) throw new OptiError(res.code);
    // 'round-trip': what the page waited for, i.e. the worker's time plus moving the pixels there and back.
    return { ...res, timings: { ...res.timings, 'round-trip': now() - t0 } };
  });
}

/** Sheet check of the data-collection page, in the worker like a measurement. */
export function checkSheet(photo: Photo): Promise<{ nMarkers?: number }> {
  return enqueue(async ({ spec }) => {
    const req: CheckRequest = { type: 'check', photo, spec };
    const res = typeof Worker === 'undefined' ? await (await import('./worker')).handleCheck(req) : await post<CheckResponse>(req, () => {});
    if (!res.ok) throw new OptiError(res.code);
    return { nMarkers: res.nMarkers };
  });
}

export async function measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement> {
  return (await run('measure', photo, eye)).result;
}

export async function measureOneDebug(photo: Photo, eye: Eye): Promise<{ result: LensMeasurement; steps: DebugSteps; timings: Timings }> {
  const res = await run('debug', photo, eye);
  if (!res.debug) throw new OptiError('LOAD_FAILED', 'no debug images');
  return { result: res.result, steps: res.debug, timings: res.timings };
}

export function finishLens(shots: LensMeasurement[]): LensMeasurement {
  try {
    return fuseShots(shots);
  } catch (e) {
    throw toOptiError(e);
  }
}
