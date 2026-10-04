// Pipeline between the screens and the heavy modules. Public API (briefs 14 and 17 import it):
//
//   measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement>
//       one photo of one lens: rectify -> segment (classic, model as fallback) -> measure.
//       Resolves with the measurement; rejects with an OptiError only (any other failure becomes LOAD_FAILED).
//   measureOneDebug(photo, eye): Promise<{ result: LensMeasurement; steps: DebugSteps }>
//       same run, plus the images of the step-by-step screen.
//   finishLens(shots: LensMeasurement[]): LensMeasurement
//       fuses 1 to 3 shots of the same lens (fuseShots); rejects with an OptiError.
//
// board_spec.json and bias.json are fetched once from public/. The work runs in a Web Worker; where there is
// none (tests, very old browsers) it runs on the calling thread through the same handleMessage.
import { OptiError, type BoardSpec, type Eye, type LensMeasurement, type Photo } from './contracts';
import type { Bias } from './measure/correction';
import { fuseShots } from './quality';
import type { DebugSteps, Step, WorkerRequest, WorkerResponse } from './worker';

export type { DebugSteps, Step } from './worker';

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

const defaultRunner: Runner = async (req, onStep) => {
  if (typeof Worker === 'undefined') {
    const { handleMessage } = await import('./worker');
    return handleMessage(req, onStep);
  }
  const w = (worker ??= new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' }));
  return new Promise<WorkerResponse>((resolve) => {
    const done = (r: WorkerResponse) => { w.onmessage = null; w.onerror = null; resolve(r); };
    w.onmessage = (e: MessageEvent<WorkerResponse | { step: Step }>) => {
      if ('step' in e.data) onStep(e.data.step);
      else done(e.data);
    };
    w.onerror = () => { w.terminate(); worker = undefined; done({ ok: false, code: 'LOAD_FAILED' }); };
    w.postMessage(req);
  });
};

function run(type: 'measure' | 'debug', photo: Photo, eye: Eye): Promise<Extract<WorkerResponse, { ok: true }>> {
  // One photo at a time: the worker has one reply slot.
  const job = queue.then(async () => {
    try {
      const { spec, bias } = await loadAssets();
      const res = await (runner ?? defaultRunner)({ type, photo, spec, eye, bias }, (s) => progress?.(s));
      if (!res.ok) throw new OptiError(res.code);
      return res;
    } catch (e) {
      throw toOptiError(e);
    }
  });
  queue = job.catch(() => {});
  return job;
}

export async function measureOne(photo: Photo, eye: Eye): Promise<LensMeasurement> {
  return (await run('measure', photo, eye)).result;
}

export async function measureOneDebug(photo: Photo, eye: Eye): Promise<{ result: LensMeasurement; steps: DebugSteps }> {
  const res = await run('debug', photo, eye);
  if (!res.debug) throw new OptiError('LOAD_FAILED', 'no debug images');
  return { result: res.result, steps: res.debug };
}

export function finishLens(shots: LensMeasurement[]): LensMeasurement {
  try {
    return fuseShots(shots);
  } catch (e) {
    throw toOptiError(e);
  }
}
