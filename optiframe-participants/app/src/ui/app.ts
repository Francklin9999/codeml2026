import { DEFAULT_FRAME, OptiError, type ErrorCode, type Eye, type FrameParams, type FrameResult, type LensMeasurement, type Photo } from '../contracts';
import { capturePhoto, isCancelled, pickFile } from '../capture';
import { FILE_NAMES, contourToSvg, measurementToJson, meshToStl, saveBlob } from '../export';
import { rotationWarningDeg } from '../measure';
import { STEP_LABELS, finishLens, loadAssets, measureOneDebug, setEngineListener, setProgressListener, toOptiError, warmUp, type DebugSteps, type EngineState, type Step, type Timings } from '../pipeline';
import { version } from '../../package.json';
import { demoError, demoMeasurement, demoPhoto, demoSteps, failWith } from './demo';
import { h } from './dom';
import { createPreview, type Preview } from './preview3d';
import { bannerView, progressView } from './chrome';
import { captureView, frameView, homeView, resultView, stepsView, type Actions, type FrameView } from './screens';
import { SHOTS_PER_LENS, initialState, restoreState, saveState, type Screen, type State } from './state';

/** Everything the screens need from outside, so tests and ?demo=1 can swap it. */
export interface Deps {
  capture(): Promise<Photo>;
  pick(): Promise<Photo>;
  measure(photo: Photo, eye: Eye): Promise<{ result: LensMeasurement; steps: DebugSteps; timings?: Timings }>;
  finish(shots: LensMeasurement[]): LensMeasurement;
  generate(left: LensMeasurement, right: LensMeasurement, p: FrameParams): Promise<FrameResult>;
  save(data: BlobPart, filename: string, mime: string): void;
  storage: Storage | null;
  /** Called with a listener for the step names; null removes it. */
  onStep(cb: ((s: Step) => void) | null): void;
  preview(host: HTMLElement): Promise<Preview | null>;
  now(): Date;
  /** Loads the sheet description and bias at start; rejects with an OptiError. */
  start(): Promise<unknown>;
  /** Starts loading the measuring tool (OpenCV.js, in the worker) in the background; cb gets its state, at once and on every change. */
  warm(cb: (s: EngineState) => void): void;
}

const now = (): number => performance.now();

function browserStorage(): Storage | null {
  try { return sessionStorage; } catch { return null; }
}

function realDeps(): Deps {
  return {
    capture: () => capturePhoto(),
    pick: () => pickFile(),
    measure: measureOneDebug,
    finish: finishLens,
    generate: async (l, r, p) => (await import('../frame')).generateFrame(l, r, p),
    save: saveBlob,
    storage: browserStorage(),
    onStep: setProgressListener,
    preview: createPreview,
    now: () => new Date(),
    start: loadAssets,
    warm: (cb) => { setEngineListener(cb); warmUp(); },
  };
}

/** ?demo=1: no camera, no sheet: synthetic measurements. ?error=CODE fails every photo with that code. */
function demoDeps(failure: ErrorCode | null): Deps {
  let n = 0;
  const shoot = async (): Promise<Photo> => (failure ? failWith(failure) : demoPhoto());
  return {
    ...realDeps(),
    capture: shoot,
    pick: shoot,
    measure: async (_photo, eye) => {
      const result = demoMeasurement(eye, n++);
      return { result, steps: demoSteps(result).steps };
    },
    storage: null, // demo numbers must never reach a real session
    onStep: () => {},
    start: async () => {},
    warm: (cb) => cb('ready'), // nothing to load: the demo never measures a photo
  };
}

export interface App { state: State; deps: Deps; render(): void }

export function startApp(root: HTMLElement, search: string, override: Partial<Deps> = {}): App {
  const params = new URLSearchParams(search);
  const demo = params.get('demo') === '1';
  const forced = demo ? demoError(search) : null;
  const deps: Deps = { ...(demo ? demoDeps(forced) : realDeps()), ...override };
  const state = initialState();
  restoreState(state, deps.storage);

  const chrome = h('div', { class: 'chrome' });
  const screenHost = h('div', { class: 'screen-host' });
  root.replaceChildren(chrome, screenHost);

  let frameUi: FrameView | null = null;
  let preview: Preview | null = null;
  let frameToken = 0;
  let frameTimer: ReturnType<typeof setTimeout> | undefined;

  // The chrome (banner, progress) can change while a screen stays: only the capture buttons depend on it.
  function renderChrome(): void {
    chrome.replaceChildren(
      ...[state.error ? bannerView(state.error, { retry, dismiss }) : null, state.busy ? progressView(state.busy) : null].filter((x): x is HTMLElement => !!x));
  }
  function refresh(): void {
    renderChrome();
    if (state.screen === 'capture') renderScreen();
  }

  function leaveFrame(): void {
    clearTimeout(frameTimer);
    frameToken++;
    preview?.dispose();
    preview = null;
    frameUi = null;
  }

  function renderScreen(): void {
    const s = state.screen;
    if (s !== 'frame') leaveFrame();
    if (s === 'frame') {
      frameUi = frameView(state, actions);
      screenHost.replaceChildren(frameUi.el);
      return;
    }
    const view = { home: homeView, capture: captureView, result: resultView, steps: stepsView }[s];
    screenHost.replaceChildren(view(state, actions));
  }

  function go(screen: Screen): void {
    state.screen = screen;
    renderChrome();
    renderScreen();
    if (typeof window !== 'undefined') try { window.scrollTo(0, 0); } catch { /* jsdom */ }
  }

  function fail(e: unknown): void {
    state.busy = null;
    state.error = toOptiError(e).code;
    refresh();
  }

  function dismiss(): void {
    state.error = null;
    refresh();
  }

  function retry(): void {
    const code = state.error;
    state.error = null;
    if (state.screen === 'frame') { renderChrome(); scheduleFrame(0); return; }
    if (code === 'INCONSISTENT_SHOTS') { state.shots = []; state.fused = null; state.hint = null; }
    go(state.eye ? 'capture' : 'home');
  }

  async function shoot(get: () => Promise<Photo>): Promise<void> {
    if (state.busy || !state.eye) return;
    state.error = null;
    const eye = state.eye;
    try {
      const photo = await get(); // may open the phone's camera: no progress yet
      state.busy = STEP_LABELS.locate;
      refresh();
      const { result, steps, timings } = await deps.measure(photo, eye);
      state.shots.push(result);
      state.last = { photo, steps, result, timings };
      state.hint = rotationWarningDeg(result) !== null ? 'LENS_ROTATED' : null;
      state.busy = null;
      if (state.shots.length >= SHOTS_PER_LENS) finishShots();
      else refresh();
    } catch (e) {
      if (isCancelled(e)) { state.busy = null; refresh(); return; } // the user closed the camera: nothing to say
      fail(e);
    }
  }

  function finishShots(): void {
    try {
      const t0 = now();
      state.fused = deps.finish(state.shots);
      state.timings.fuse = now() - t0;
      state.busy = null;
      go('result');
    } catch (e) {
      fail(e);
    }
  }

  // ---- frame screen ----
  function scheduleFrame(delay: number): void {
    clearTimeout(frameTimer);
    frameTimer = setTimeout(() => void buildFrame(), delay);
  }

  async function buildFrame(): Promise<void> {
    const { L, R } = state.lenses;
    if (!L || !R || !frameUi) return;
    const token = ++frameToken;
    const ui = frameUi;
    ui.setBusy(true);
    try {
      const t0 = now();
      const f = await deps.generate(L, R, { ...DEFAULT_FRAME, bridgeMm: state.bridgeMm });
      if (token !== frameToken) return; // a newer slider value won
      state.timings.frame = now() - t0; // the first one includes loading the generator and its WASM
      state.frame = f;
      ui.showFrame(f);
      preview?.update(f);
    } catch (e) {
      if (token === frameToken) fail(e);
    } finally {
      if (token === frameToken) ui.setBusy(false);
    }
  }

  async function openFrame(): Promise<void> {
    if (!state.lenses.L || !state.lenses.R) return;
    state.frame = null;
    go('frame');
    const ui = frameUi!;
    scheduleFrame(0);
    const p = await deps.preview(ui.preview);
    if (frameUi !== ui) { p?.dispose(); return; } // the user already left
    if (!p) { ui.preview.textContent = 'Aperçu 3D indisponible sur cet appareil. Le fichier STL reste disponible.'; return; }
    preview = p;
    if (state.frame) p.update(state.frame);
  }

  const download = (make: () => [BlobPart, string, string]) => () => {
    try { deps.save(...make()); } catch (e) { fail(e); }
  };

  const actions: Actions = {
    chooseEye(eye) { state.eye = eye; state.shots = []; state.fused = null; state.hint = null; state.error = null; go('capture'); warm(); },
    takePhoto() { void shoot(deps.capture); },
    importPhoto() { void shoot(deps.pick); },
    finishShots,
    exportSvg: download(() => {
      const m = state.fused;
      if (!m) throw new OptiError('NO_LENS');
      return [contourToSvg(m), m.eye === 'L' ? FILE_NAMES.svgLeft : FILE_NAMES.svgRight, 'image/svg+xml'];
    }),
    exportSvgOf: (eye) => download(() => {
      const m = state.lenses[eye];
      if (!m) throw new OptiError('NO_LENS');
      return [contourToSvg(m), eye === 'L' ? FILE_NAMES.svgLeft : FILE_NAMES.svgRight, 'image/svg+xml'];
    })(),
    retake() { state.shots = []; state.fused = null; state.hint = null; state.error = null; go('capture'); },
    validate() {
      const m = state.fused;
      if (!m) return;
      state.lenses[m.eye] = m;
      state.frame = null;
      saveState(state, deps.storage);
      state.shots = []; state.fused = null; state.hint = null; state.eye = null;
      go('home');
    },
    goHome() { state.error = null; go('home'); },
    showSteps() { go('steps'); },
    openFrame() { void openFrame(); },
    setBridge(mm) { state.bridgeMm = mm; saveState(state, deps.storage); scheduleFrame(200); },
    downloadStl: download(() => {
      if (!state.frame) throw new OptiError('NO_LENS');
      const t0 = now();
      const stl = meshToStl(state.frame);
      state.timings.stl = now() - t0;
      return [stl, FILE_NAMES.stl, 'model/stl'];
    }),
    downloadJson: download(() => {
      const { L, R } = state.lenses;
      if (!L || !R) throw new OptiError('NO_LENS');
      return [measurementToJson(L, R, { ...DEFAULT_FRAME, bridgeMm: state.bridgeMm }, version, deps.now().toISOString().slice(0, 10)), FILE_NAMES.json, 'application/json'];
    }),
  };

  // The measuring tool loads in the background from the home screen on; the capture screen says so while it is not ready.
  function warm(): void {
    if (state.engine === 'loading' || state.engine === 'ready') return;
    deps.warm((e) => {
      if (e === state.engine) return;
      state.engine = e;
      if (state.screen === 'capture') renderScreen();
    });
  }

  deps.onStep((step) => { state.busy = STEP_LABELS[step]; refresh(); });
  go('home');
  warm();
  if (forced) fail(new OptiError(forced, 'demo')); // the same path as a real failure
  else if (!demo) void deps.start().catch(fail);

  return { state, deps, render: () => go(state.screen) };
}
