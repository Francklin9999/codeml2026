import { OptiError, PX_PER_MM, type Mask, type Rectified } from '../contracts';

// Browser fallback segmenter. Pre and post-processing are pure typed-array code (no DOM, no
// OffscreenCanvas) so they run in a worker and in Node tests. Model interface: see brief 12.
export const MODEL_PATH = 'models/lens_seg.onnx'; // fixed: the service worker caches /models/ cache-first
export const ORT_WASM_DIR = 'vendor/ort/';
export const MODEL_W = 384;
export const MODEL_H = 320;
export const MEAN = [0.485, 0.456, 0.406] as const;
export const STD = [0.229, 0.224, 0.225] as const;
export const MASK_THRESHOLD = 0.5;
/** Below this mean probability inside the mask the model is guessing: NO_LENS, never a measurement. On the
 *  synthetic test windows (training/data/synth_rig.py, 1500 images) every lens mask within 1 mm scored >= 0.94 and
 *  every lens invented on an empty window scored 0.64 to 0.71. Real-photo value: TO MEASURE. */
export const MIN_MODEL_SCORE = 0.85;
// Same plausibility limits as the classical segmenter.
export const MIN_LENS_AREA_MM2 = 600;
export const MAX_LENS_AREA_MM2 = 4000;

export interface Timings { loadMs: number; preMs: number; runMs: number; postMs: number }
/** What the pipeline needs from a model: float32 CHW input in, flat logits out. Tests pass a fake. */
export interface ModelSession { run(input: Float32Array, dims: readonly number[]): Promise<ArrayLike<number>> }
type RasterLike = { data: ArrayLike<number>; width: number; height: number };

const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());

/** Bilinear resample with half-pixel centres, `ch` interleaved channels, edge clamped. */
export function resizeBilinear(src: ArrayLike<number>, sw: number, sh: number, ch: number, dw: number, dh: number): Float32Array {
  const out = new Float32Array(dw * dh * ch);
  const fx = sw / dw, fy = sh / dh;
  for (let y = 0; y < dh; y++) {
    const sy = Math.min(Math.max((y + 0.5) * fy - 0.5, 0), sh - 1);
    const y0 = Math.floor(sy), y1 = Math.min(y0 + 1, sh - 1), wy = sy - y0;
    for (let x = 0; x < dw; x++) {
      const sx = Math.min(Math.max((x + 0.5) * fx - 0.5, 0), sw - 1);
      const x0 = Math.floor(sx), x1 = Math.min(x0 + 1, sw - 1), wx = sx - x0;
      for (let c = 0; c < ch; c++) {
        const top = src[(y0 * sw + x0) * ch + c] * (1 - wx) + src[(y0 * sw + x1) * ch + c] * wx;
        const bot = src[(y1 * sw + x0) * ch + c] * (1 - wx) + src[(y1 * sw + x1) * ch + c] * wx;
        out[(y * dw + x) * ch + c] = top * (1 - wy) + bot * wy;
      }
    }
  }
  return out;
}

/** RGBA image -> float32 1x3xHxW (planar RGB, 0-1 then mean/std normalised). Alpha is ignored. */
export function preprocess(img: RasterLike): Float32Array {
  const rgba = resizeBilinear(img.data, img.width, img.height, 4, MODEL_W, MODEL_H);
  const plane = MODEL_W * MODEL_H;
  const out = new Float32Array(3 * plane);
  for (let i = 0; i < plane; i++) {
    for (let c = 0; c < 3; c++) out[c * plane + i] = (rgba[i * 4 + c] / 255 - MEAN[c]) / STD[c];
  }
  return out;
}

/** 4-connected component with the most pixels, as a new 0/1 array (all zero if none). */
export function largestComponent(bin: Uint8Array, w: number, h: number): Uint8Array {
  const label = new Int32Array(w * h);
  const stack = new Int32Array(w * h);
  let best = 0, bestSize = 0, n = 0;
  for (let s = 0; s < bin.length; s++) {
    if (!bin[s] || label[s]) continue;
    n++;
    let size = 0, top = 0;
    stack[top++] = s;
    label[s] = n;
    while (top) {
      const p = stack[--top];
      size++;
      const x = p % w;
      if (x > 0 && bin[p - 1] && !label[p - 1]) { label[p - 1] = n; stack[top++] = p - 1; }
      if (x < w - 1 && bin[p + 1] && !label[p + 1]) { label[p + 1] = n; stack[top++] = p + 1; }
      if (p >= w && bin[p - w] && !label[p - w]) { label[p - w] = n; stack[top++] = p - w; }
      if (p < w * (h - 1) && bin[p + w] && !label[p + w]) { label[p + w] = n; stack[top++] = p + w; }
    }
    if (size > bestSize) { best = n; bestSize = size; }
  }
  const out = new Uint8Array(w * h);
  if (best) for (let i = 0; i < out.length; i++) if (label[i] === best) out[i] = 1;
  return out;
}

/** Sets to 1 every 0 pixel that cannot reach the image border through 0 pixels (4-connected). */
export function fillHoles(mask: Uint8Array, w: number, h: number): Uint8Array {
  const outside = new Uint8Array(w * h);
  const stack = new Int32Array(w * h);
  let top = 0;
  const seed = (p: number) => { if (!mask[p] && !outside[p]) { outside[p] = 1; stack[top++] = p; } };
  for (let x = 0; x < w; x++) { seed(x); seed((h - 1) * w + x); }
  for (let y = 0; y < h; y++) { seed(y * w); seed(y * w + w - 1); }
  while (top) {
    const p = stack[--top];
    const x = p % w;
    if (x > 0) seed(p - 1);
    if (x < w - 1) seed(p + 1);
    if (p >= w) seed(p - w);
    if (p < w * (h - 1)) seed(p + w);
  }
  const out = new Uint8Array(w * h);
  for (let i = 0; i < out.length; i++) out[i] = outside[i] ? 0 : 1;
  return out;
}

/** Flat logits (MODEL_H x MODEL_W) -> mask of size w x h. Throws NO_LENS or LENS_OUT_OF_WINDOW. */
export function postprocess(logits: ArrayLike<number>, w: number, h: number, pxPerMm: number = PX_PER_MM): Mask {
  if (logits.length !== MODEL_W * MODEL_H) throw new OptiError('LOAD_FAILED', 'unexpected model output size ' + logits.length);
  const prob = new Float32Array(MODEL_W * MODEL_H);
  for (let i = 0; i < prob.length; i++) prob[i] = 1 / (1 + Math.exp(-logits[i]));
  const full = resizeBilinear(prob, MODEL_W, MODEL_H, 1, w, h);
  const bin = new Uint8Array(w * h);
  for (let i = 0; i < bin.length; i++) bin[i] = full[i] > MASK_THRESHOLD ? 1 : 0;
  const data = fillHoles(largestComponent(bin, w, h), w, h);

  let count = 0, sum = 0, touchesBorder = false;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      if (!data[i]) continue;
      count++;
      sum += full[i];
      if (x === 0 || y === 0 || x === w - 1 || y === h - 1) touchesBorder = true;
    }
  }
  const areaMm2 = count / (pxPerMm * pxPerMm);
  if (areaMm2 < MIN_LENS_AREA_MM2 || areaMm2 > MAX_LENS_AREA_MM2) throw new OptiError('NO_LENS', `model mask area ${areaMm2.toFixed(0)} mm2`);
  const score = sum / count;
  if (score < MIN_MODEL_SCORE) throw new OptiError('NO_LENS', `model not confident (${score.toFixed(2)})`);
  if (touchesBorder) throw new OptiError('LENS_OUT_OF_WINDOW', 'model mask touches the window border');
  return { data, width: w, height: h, method: 'model', score };
}

// ---- session handling (lazy, once) ----

let sessionPromise: Promise<ModelSession> | null = null;
let timings: Timings = { loadMs: 0, preMs: 0, runMs: 0, postMs: 0 };
let loadMs = 0;
let assetBase: string | null = null;
/** Answer of the one HEAD request for the model file. Unset until a server has answered. */
let modelExists: boolean | undefined;

/** Override where `vendor/` and `models/` live (absolute URL ending in `/`). Default: the app root. */
export function setAssetBase(url: string | null): void {
  assetBase = url;
  sessionPromise = null;
  modelExists = undefined;
}

function appRoot(): string {
  if (assetBase) return assetBase;
  if (typeof document !== 'undefined') return document.baseURI;
  // In a worker the script lives in assets/ (build) or src/ (dev): the app root is one level up.
  return new URL('../', (globalThis as { location?: { href: string } }).location?.href ?? 'http://localhost/').href;
}

// A dev server answers a missing file with index.html and status 200: treat it as missing too.
const isFile = (res: Response): boolean => res.ok && !/text\/html/i.test(res.headers.get('content-type') ?? '');

/**
 * Is models/lens_seg.onnx deployed? One HEAD request (no body), asked once: the answer is kept for the session, so a
 * site without a model never downloads the model, onnxruntime-web or its 14 MB WASM. A network failure is not an
 * answer: it rejects and the next call asks again.
 */
async function probeModel(root: string): Promise<boolean> {
  if (modelExists === undefined) {
    const answer = isFile(await fetch(new URL(MODEL_PATH, root).href, { method: 'HEAD' }));
    modelExists = answer;
  }
  return modelExists;
}

async function loadOrt(): Promise<ModelSession> {
  const root = appRoot();
  if (!(await probeModel(root))) throw new OptiError('LOAD_FAILED', 'model not found');
  const res = await fetch(new URL(MODEL_PATH, root).href);
  if (!isFile(res)) throw new OptiError('LOAD_FAILED', `model not found (${res.status})`);
  const bytes = new Uint8Array(await res.arrayBuffer());
  // Only reached with the model in hand: the runtime is a separate chunk and its WASM is fetched by this import.
  const ort = await import('onnxruntime-web/wasm');
  ort.env.wasm.numThreads = 1; // static hosts cannot send the headers threads need
  ort.env.wasm.proxy = false;
  ort.env.wasm.wasmPaths = new URL(ORT_WASM_DIR, root).href;
  const session = await ort.InferenceSession.create(bytes, { executionProviders: ['wasm'], graphOptimizationLevel: 'all' });
  return {
    async run(input, dims) {
      const out = await session.run({ input: new ort.Tensor('float32', input, dims as number[]) });
      return out.logits.data as Float32Array;
    },
  };
}

function getSession(): Promise<ModelSession> {
  if (!sessionPromise) {
    const t0 = now();
    sessionPromise = loadOrt().then(
      (s) => { loadMs = now() - t0; return s; },
      (e) => {
        sessionPromise = null; // let a later call retry (offline first load, model deployed later)
        throw e instanceof OptiError ? e : new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e));
      },
    );
  }
  return sessionPromise;
}

/** True when the model file and runtime load. Never rejects. */
export async function isModelAvailable(): Promise<boolean> {
  try {
    await getSession();
    return true;
  } catch {
    return false;
  }
}

/** Timings of the last run. loadMs is the one-off session load, kept so a UI can show it. */
export function getLastTimings(): Timings {
  return { ...timings };
}

/** Tests only: use a fake session instead of fetching the model. */
export function setSessionForTests(s: ModelSession | null, loadTimeMs = 0): void {
  sessionPromise = s ? Promise.resolve(s) : null;
  loadMs = loadTimeMs;
}

export async function segmentModel(r: Rectified): Promise<Mask> {
  try {
    const session = await getSession();
    const t0 = now();
    const input = preprocess(r.image);
    const t1 = now();
    const logits = await session.run(input, [1, 3, MODEL_H, MODEL_W]);
    const t2 = now();
    const mask = postprocess(logits, r.image.width, r.image.height, r.pxPerMm);
    timings = { loadMs, preMs: t1 - t0, runMs: t2 - t1, postMs: now() - t2 };
    return mask;
  } catch (e) {
    throw e instanceof OptiError ? e : new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e));
  }
}
