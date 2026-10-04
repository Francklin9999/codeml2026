// ?demo=1: built-in synthetic data so the five screens can be walked without a camera.
// Every number here is made up for the demo, none is a measurement.
import { OptiError, PX_PER_MM, type ErrorCode, type Eye, type LensMeasurement, type Photo, type Pt } from '../contracts';
import { boxing } from '../measure/boxing';
import type { DebugSteps } from '../worker';

export const ERROR_CODES: ErrorCode[] = ['NO_REFERENCE', 'REFERENCE_TILTED', 'BLURRY', 'NO_LENS', 'LENS_OUT_OF_WINDOW', 'GLARE', 'INCONSISTENT_SHOTS', 'LENS_ROTATED', 'CAMERA_DENIED', 'LOAD_FAILED'];

/** The code asked for by ?error=, when it is a known one. */
export function demoError(search: string): ErrorCode | null {
  const v = new URLSearchParams(search).get('error');
  return ERROR_CODES.find((c) => c === v) ?? null;
}

const WIN: Pt = [80, 65];
// Synthetic half-axes in mm: the two lenses differ a little so the frame is not symmetric.
const AXES: Record<Eye, Pt> = { R: [26.2, 20.8], L: [25.9, 20.6] };
const WOBBLE = [0.0, 0.08, -0.06]; // between shots, so the spread line has something to show

function ellipse(a: number, b: number): Pt[] {
  const pts: Pt[] = [];
  const n = 720;
  for (let i = 0; i < n; i++) {
    const t = (2 * Math.PI * i) / n;
    pts.push([WIN[0] / 2 + a * Math.cos(t), WIN[1] / 2 + b * Math.sin(t)]);
  }
  return pts;
}

export function demoMeasurement(eye: Eye, shot: number): LensMeasurement {
  const w = WOBBLE[shot % WOBBLE.length];
  const [a, b] = AXES[eye];
  const contourMm = ellipse(a + w, b - w / 2);
  const { A, B, boxCentre, perimeter } = boxing(contourMm);
  return { eye, contourMm, A, B, perimeter, boxCentre, method: 'classic', quality: { reprojErrMm: 0.1, sharpness: 0.001, nShots: 1, spreadA: 0, spreadB: 0 } };
}

function grey(w: number, h: number, f: (x: number, y: number) => number): ImageData {
  const d = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = (y * w + x) * 4;
    d[i] = d[i + 1] = d[i + 2] = f(x, y);
    d[i + 3] = 255;
  }
  return new ImageData(d, w, h);
}

/** Small synthetic photo, rectified window, mask and marker squares for the step-by-step screen. */
export function demoSteps(m: LensMeasurement): { photo: Photo; steps: DebugSteps } {
  const [a, b] = AXES[m.eye];
  const w = WIN[0] * PX_PER_MM, h = WIN[1] * PX_PER_MM;
  const inside = (x: number, y: number, k: number) => ((x / PX_PER_MM - WIN[0] / 2) / (a + k)) ** 2 + ((y / PX_PER_MM - WIN[1] / 2) / (b + k)) ** 2 <= 1;
  const rectified = grey(w, h, (x, y) => (inside(x, y, 0) ? (inside(x, y, -2.5) ? 232 : 28) : 252));
  const data = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) data[y * w + x] = inside(x, y, 0) ? 1 : 0;
  const photo: Photo = { image: grey(320, 240, (x, y) => 200 + ((x + y) % 40)), source: 'file' };
  const square = (x: number, y: number): Pt[] => [[x, y], [x + 30, y], [x + 30, y + 30], [x, y + 30]];
  const markers = [square(20, 20), square(270, 20), square(270, 190), square(20, 190)];
  return { photo, steps: { markers, rectified, mask: { data, width: w, height: h, method: 'classic', score: 1 } } };
}

export function demoPhoto(): Photo {
  return { image: new ImageData(4, 4), source: 'file' };
}

/** Throws the code the way a real failure does. */
export function failWith(code: ErrorCode): never {
  throw new OptiError(code, 'demo');
}
