import { OptiError, type Photo } from '../contracts';
import { parseExif } from './exif';
import { fitSize, orientationMatrix } from './geometry';

export interface CaptureOptions {
  /** getUserMedia path instead of the native camera sheet. Must be called from a user gesture. */
  useLiveCamera?: boolean;
  /** Live path only: resolves when the user presses the shutter. Default: grab as soon as a frame is ready. */
  waitForShutter?: () => Promise<void>;
}

interface Ctx2D {
  setTransform(a: number, b: number, c: number, d: number, e: number, f: number): void;
  drawImage(img: any, dx: number, dy: number): void;
  getImageData(x: number, y: number, w: number, h: number): ImageData;
}
interface Canvas { getContext(kind: '2d'): Ctx2D | null }

/** Browser services, replaceable in tests. */
export interface CaptureEnv {
  document: Document;
  mediaDevices?: Pick<MediaDevices, 'getUserMedia'>;
  createImageBitmap: (src: Blob, opts?: { imageOrientation?: string }) => Promise<ImageBitmap>;
  makeCanvas: (w: number, h: number) => Canvas;
  ImageCapture?: new (track: MediaStreamTrack) => { takePhoto(): Promise<Blob> };
}

export function browserEnv(): CaptureEnv {
  const g = globalThis as any;
  return {
    document: g.document,
    mediaDevices: g.navigator?.mediaDevices,
    createImageBitmap: (s, o) => g.createImageBitmap(s, o),
    makeCanvas: (w, h) => {
      if (typeof g.OffscreenCanvas === 'function') return new g.OffscreenCanvas(w, h);
      const c = g.document.createElement('canvas');
      c.width = w;
      c.height = h;
      return c;
    },
    ImageCapture: g.ImageCapture,
  };
}

export function capturePhoto(opts: CaptureOptions = {}, env: CaptureEnv = browserEnv()): Promise<Photo> {
  return wrap(async () => {
    if (opts.useLiveCamera) return liveShot(env, opts);
    return decode(await chooseFile(env, true), 'camera', env);
  });
}

export function pickFile(env: CaptureEnv = browserEnv()): Promise<Photo> {
  return wrap(async () => decode(await chooseFile(env, false), 'file', env));
}

/** Data-collection page: the original file, bytes untouched (EXIF, focal length), from the native camera or the gallery. */
export function chooseOriginalFile(camera: boolean, env: CaptureEnv = browserEnv()): Promise<File> {
  return wrap(() => chooseFile(env, camera));
}

/** Data-collection page: decode a file chosen earlier into the Photo the pipeline expects. */
export function decodeFile(file: Blob, source: Photo['source'] = 'file', env: CaptureEnv = browserEnv()): Promise<Photo> {
  return wrap(() => decode(file, source, env));
}

async function wrap<T>(f: () => Promise<T>): Promise<T> {
  try {
    return await f();
  } catch (e) {
    if (e instanceof OptiError) throw e;
    throw new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e));
  }
}

function chooseFile(env: CaptureEnv, camera: boolean): Promise<File> {
  return new Promise((resolve, reject) => {
    const input = env.document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    if (camera) input.setAttribute('capture', 'environment');
    input.style.display = 'none';
    const done = (fn: () => void) => {
      input.removeEventListener('change', onChange);
      input.removeEventListener('cancel', onCancel);
      input.remove();
      fn();
    };
    const onChange = () => {
      const f = input.files?.[0];
      done(() => (f ? resolve(f) : reject(new OptiError('LOAD_FAILED', 'no file chosen'))));
    };
    const onCancel = () => done(() => reject(new OptiError('LOAD_FAILED', 'cancelled')));
    input.addEventListener('change', onChange);
    input.addEventListener('cancel', onCancel);
    env.document.body.appendChild(input);
    input.click();
  });
}

async function liveShot(env: CaptureEnv, opts: CaptureOptions): Promise<Photo> {
  if (!env.mediaDevices) throw new OptiError('LOAD_FAILED', 'getUserMedia unavailable');
  let stream: MediaStream;
  try {
    stream = await env.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 4032 }, height: { ideal: 3024 } },
      audio: false,
    });
  } catch (e) {
    const name = (e as { name?: string })?.name;
    if (name === 'NotAllowedError' || name === 'SecurityError') throw new OptiError('CAMERA_DENIED', name);
    throw new OptiError('LOAD_FAILED', name ?? 'getUserMedia failed');
  }
  const video = env.document.createElement('video');
  try {
    video.setAttribute('playsinline', '');
    video.muted = true;
    video.srcObject = stream;
    video.style.display = 'none';
    env.document.body.appendChild(video);
    await video.play();
    await opts.waitForShutter?.();
    const track = stream.getVideoTracks()[0];
    if (env.ImageCapture && track) {
      let blob: Blob | undefined;
      try { blob = await new env.ImageCapture(track).takePhoto(); } catch { /* use the frame instead */ }
      if (blob) return await decode(blob, 'camera', env);
    }
    const w = video.videoWidth, h = video.videoHeight;
    if (!w || !h) throw new OptiError('LOAD_FAILED', 'no video frame');
    return { image: render(env, video, w, h, 1), source: 'camera' };
  } finally {
    stream.getTracks().forEach((t) => t.stop());
    video.srcObject = null;
    video.remove();
  }
}

/** Draw a source upright (EXIF orientation `o` still to apply) at the downscaled size and read it back. */
function render(env: CaptureEnv, src: unknown, srcW: number, srcH: number, o: number): ImageData {
  const turn = o >= 5;
  const upW = turn ? srcH : srcW, upH = turn ? srcW : srcH;
  const { w, h } = fitSize(upW, upH);
  const ctx = env.makeCanvas(w, h).getContext('2d');
  if (!ctx) throw new OptiError('LOAD_FAILED', 'no 2d context');
  const [a, b, c, d, e, f] = orientationMatrix(o, srcW, srcH);
  const sx = w / upW, sy = h / upH;
  ctx.setTransform(a * sx, b * sy, c * sx, d * sy, e * sx, f * sy);
  ctx.drawImage(src, 0, 0);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  return ctx.getImageData(0, 0, w, h);
}

async function decode(file: Blob, source: Photo['source'], env: CaptureEnv): Promise<Photo> {
  const exif = parseExif(new Uint8Array(await file.slice(0, 262144).arrayBuffer()));
  let bitmap: ImageBitmap;
  let manual = exif.orientation; // EXIF rotation still to apply by hand
  try {
    bitmap = await env.createImageBitmap(file, { imageOrientation: 'from-image' });
    manual = 1;
    // A browser that ignores the option returns the raw pixel grid: detectable when the tag swaps the axes.
    const swaps = exif.orientation >= 5 && !!exif.width && !!exif.height && exif.width !== exif.height;
    if (swaps && bitmap.width === exif.width && bitmap.height === exif.height) manual = exif.orientation;
  } catch {
    try { bitmap = await env.createImageBitmap(file); } catch { throw new OptiError('LOAD_FAILED', 'cannot decode image'); }
  }
  try {
    const photo: Photo = { image: render(env, bitmap, bitmap.width, bitmap.height, manual), source };
    if (exif.focal35mm) photo.focal35mm = exif.focal35mm;
    return photo;
  } finally {
    bitmap.close?.();
  }
}
