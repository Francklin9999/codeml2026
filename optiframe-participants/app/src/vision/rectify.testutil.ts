// Synthetic photographs of the reference sheet, for tests only (never imported by app code).
import type { BoardSpec, Photo, Pt } from '../contracts';
import { loadOpenCv } from './opencv';

export const PAPER = 230;
export const INK = 25;
const R = 24; // board raster density, px per mm (15 mm marker = 360 px = 6 cells of 60)

/** A 180 x 150 mm sheet: 80 x 65 mm window and 14 markers of 15 mm around it, ids 0..13. */
export function defaultSpec(printScale = 1): BoardSpec {
  const m = 15;
  const pos: Pt[] = [];
  // top row y=-25, bottom row y=75, x steps of 25 from -45 to 105
  for (const x of [-45, -20, 5, 30, 55, 80, 105]) { pos.push([x, -25]); }
  for (const x of [-45, -20, 5, 30, 55, 80, 105]) { pos.push([x, 75]); }
  const markers = pos.map((p, id) => ({
    id,
    corners: [[p[0], p[1]], [p[0] + m, p[1]], [p[0] + m, p[1] + m], [p[0], p[1] + m]] as Pt[],
  }));
  return { dictionary: 'DICT_4X4_50', markerMm: m, markers, windowMm: { w: 80, h: 65 }, guideLineYMm: 32.5, rulerMm: 100, printScale };
}

export interface SceneOptions {
  width?: number; height?: number;
  f35?: number;            // 35 mm equivalent focal length used to build the camera
  distMm?: number;         // camera to window-centre distance along the optical axis
  tiltDeg?: number;        // rotation of the camera about the board x axis
  panDeg?: number;         // about the board y axis
  rollDeg?: number;        // about the optical axis
  shiftMm?: Pt;            // aiming error: window centre appears off the principal point
  supersample?: number;    // render at n x then average down (default 2)
  blurSigma?: number;      // Gaussian blur of the photo, px
  noiseSigma?: number;     // grey levels
  radialK?: number;        // barrel distortion applied to the photo (residual that no homography can absorb)
  draw?: (ctx: BoardCanvas) => void;
  occlude?: (img: Uint8Array, w: number, h: number) => void;
}

/** Draws on the board raster in board millimetres. */
export interface BoardCanvas {
  rect(x0: number, y0: number, x1: number, y1: number, grey: number): void;
}

export interface Scene { photo: Photo; Htrue: number[]; fPx: number; trueDistMm: number; grey: Uint8Array }

function rot(axis: 'x' | 'y' | 'z', deg: number): number[] {
  const a = (deg * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a);
  if (axis === 'x') return [1, 0, 0, 0, c, -s, 0, s, c];
  if (axis === 'y') return [c, 0, s, 0, 1, 0, -s, 0, c];
  return [c, -s, 0, s, c, 0, 0, 0, 1];
}
function mm3(a: number[], b: number[]): number[] {
  const r = new Array(9).fill(0);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) for (let k = 0; k < 3; k++) r[i * 3 + j] += a[i * 3 + k] * b[k * 3 + j];
  return r;
}

function gauss(rand: () => number) {
  return Math.sqrt(-2 * Math.log(rand() + 1e-12)) * Math.cos(2 * Math.PI * rand());
}
function lcg(seed: number) {
  let s = seed >>> 0;
  return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296);
}

export async function renderScene(spec: BoardSpec, o: SceneOptions = {}): Promise<Scene> {
  const cv = await loadOpenCv();
  const W = o.width ?? 3200, Hh = o.height ?? 2400;
  const ss = o.supersample ?? 2;
  const f35 = o.f35 ?? 26;
  const D = o.distMm ?? 200;
  const ps = spec.printScale;
  const fPx = (f35 / 36) * Math.max(W, Hh);

  // Board raster: paper, markers, optional drawings. Physical mm = nominal mm * printScale.
  const xs = spec.markers.flatMap((m) => m.corners.map((c) => c[0]));
  const ys = spec.markers.flatMap((m) => m.corners.map((c) => c[1]));
  const x0 = Math.floor(Math.min(0, ...xs) / 5) * 5 - 15, x1 = Math.ceil(Math.max(spec.windowMm.w, ...xs) / 5) * 5 + 15;
  const y0 = Math.floor(Math.min(0, ...ys) / 5) * 5 - 15, y1 = Math.ceil(Math.max(spec.windowMm.h, ...ys) / 5) * 5 + 15;
  const rw = (x1 - x0) * R, rh = (y1 - y0) * R;
  const raster = new Uint8Array(rw * rh).fill(PAPER);
  const rect = (ax: number, ay: number, bx: number, by: number, grey: number) => {
    const ia = Math.round((ax - x0) * R), ja = Math.round((ay - y0) * R), ib = Math.round((bx - x0) * R), jb = Math.round((by - y0) * R);
    for (let j = ja; j < jb; j++) raster.fill(grey, j * rw + ia, j * rw + ib);
  };
  const dict = cv.getPredefinedDictionary((cv as unknown as Record<string, number>)[spec.dictionary]);
  const side = Math.round(spec.markerMm * R);
  const tile = new cv.Mat();
  for (const m of spec.markers) {
    cv.generateImageMarker(dict, m.id, side, tile, 1);
    const ia = Math.round((m.corners[0][0] - x0) * R), ja = Math.round((m.corners[0][1] - y0) * R);
    for (let j = 0; j < side; j++) for (let i = 0; i < side; i++) raster[(ja + j) * rw + ia + i] = tile.data[j * side + i] ? PAPER : INK;
  }
  tile.delete(); dict.delete();
  o.draw?.({ rect });

  // Camera: Xc = Rot * (X - C) + (shift, D), C = window centre (physical mm); H = K [r1 r2 t].
  const sh = o.shiftMm ?? [0, 0];
  const rm = mm3(mm3(rot('z', o.rollDeg ?? 0), rot('x', o.tiltDeg ?? 0)), rot('y', o.panDeg ?? 0));
  const cx = (spec.windowMm.w * ps) / 2, cy = (spec.windowMm.h * ps) / 2;
  const t = [-(rm[0] * cx + rm[1] * cy) + sh[0], -(rm[3] * cx + rm[4] * cy) + sh[1], -(rm[6] * cx + rm[7] * cy) + D];
  const px = W / 2, py = Hh / 2;
  const cam = [fPx * rm[0] + px * rm[6], fPx * rm[1] + px * rm[7], fPx * t[0] + px * t[2],
    fPx * rm[3] + py * rm[6], fPx * rm[4] + py * rm[7], fPx * t[1] + py * t[2],
    rm[6], rm[7], t[2]];
  const Htrue = cam.map((v) => v / cam[8]);

  // raster pixel (i, j), centre-at-integer convention -> physical mm: ((i + .5)/R + x0) * ps
  const S = [ps / R, 0, (0.5 / R + x0) * ps, 0, ps / R, (0.5 / R + y0) * ps, 0, 0, 1];
  // image coordinate (x, y) -> supersampled image coordinate (ss*x + (ss-1)/2)
  const A = [ss, 0, (ss - 1) / 2, 0, ss, (ss - 1) / 2, 0, 0, 1];
  const Wm = mm3(A, mm3(Htrue, S));
  const src = new cv.Mat(rh, rw, cv.CV_8UC1);
  src.data.set(raster);
  const big = new cv.Mat();
  const M = cv.matFromArray(3, 3, cv.CV_64F, Wm);
  cv.warpPerspective(src, big, M, new cv.Size(W * ss, Hh * ss), cv.INTER_LINEAR, cv.BORDER_CONSTANT, new cv.Scalar(100));
  const img = new cv.Mat();
  if (ss > 1) cv.resize(big, img, new cv.Size(W, Hh), 0, 0, cv.INTER_AREA); else big.copyTo(img);
  src.delete(); big.delete(); M.delete();

  if (o.radialK) {
    const mapx = new cv.Mat(Hh, W, cv.CV_32FC1), mapy = new cv.Mat(Hh, W, cv.CV_32FC1);
    const rn = Math.hypot(W, Hh) / 2;
    for (let y = 0; y < Hh; y++) for (let x = 0; x < W; x++) {
      const dx = (x - px) / rn, dy = (y - py) / rn, k = 1 + o.radialK * (dx * dx + dy * dy);
      mapx.floatPtr(y, x)[0] = px + dx * rn * k; mapy.floatPtr(y, x)[0] = py + dy * rn * k;
    }
    const out = new cv.Mat();
    cv.remap(img, out, mapx, mapy, cv.INTER_LINEAR, cv.BORDER_CONSTANT, new cv.Scalar(100));
    out.copyTo(img); out.delete(); mapx.delete(); mapy.delete();
  }
  if (o.blurSigma) {
    const b = new cv.Mat();
    cv.GaussianBlur(img, b, new cv.Size(0, 0), o.blurSigma, o.blurSigma);
    b.copyTo(img); b.delete();
  }
  const grey = new Uint8Array(img.data);
  img.delete();
  o.occlude?.(grey, W, Hh);
  if (o.noiseSigma) {
    const rand = lcg(12345);
    for (let i = 0; i < grey.length; i++) grey[i] = Math.max(0, Math.min(255, Math.round(grey[i] + gauss(rand) * o.noiseSigma)));
  }
  const rgba = new Uint8ClampedArray(W * Hh * 4);
  for (let i = 0; i < grey.length; i++) { const g = grey[i]; rgba[4 * i] = g; rgba[4 * i + 1] = g; rgba[4 * i + 2] = g; rgba[4 * i + 3] = 255; }
  const photo: Photo = { image: new ImageData(rgba, W, Hh), source: 'file', focal35mm: f35 };
  return { photo, Htrue, fPx, trueDistMm: Math.hypot(sh[0], sh[1], D), grey };
}
