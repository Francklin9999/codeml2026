import { OptiError, PX_PER_MM, type BoardSpec, type Photo, type Pt, type Rectified } from '../contracts';
import { applyH, invert3, mul3, ransacHomography, type Mat3 } from './homography';
import { loadOpenCv, type Cv } from './opencv';
import { timed, timedAsync } from '../timing';

// Frames. Board frame: mm, origin at the window's top-left corner, spec coordinates times spec.printScale
// give physical mm. Photo pixels: centre of pixel (i, j) is at (i, j), as in OpenCV.
// Rectified image: physical mm, pixel (i, j) covers [i, i+1) / PX_PER_MM, so the window's top-left corner is
// the top-left corner of pixel (0, 0). H (board -> photo px) is stored in Rectified.H.

/** Highest accepted RMS residual of the marker corners, mm. Provisional. Target of strat2 section 4.2: 0.1 mm, TO MEASURE. */
export const MAX_REPROJ_MM = 0.3;
/** Reference plane tilted more than this away from the optical axis is rejected. */
export const MAX_TILT_DEG = 35;
/**
 * Rectified.sharpness below which the photo is BLURRY. Scale: median over the reference markers of patchSharpness (dimensionless,
 * higher = sharper, about 0.05 for a crisp synthetic photo). The photo-pixel blur of a scene depends on its resolution, so the
 * scale is physical: markers are measured at 10 px/mm. Derivation, from this repo's synthetic runs only: Gaussian blur of the whole
 * photo (11.5 photo px/mm) gives 0.0059 / 0.0010 / 0.00028 / 0.00011 / 0.00003 for sigma 1 / 2 / 3 / 4 / 6 px (0.09 .. 0.52 mm), and
 * the rig fixtures (blur 0.7-1.5 px at 5.5 px/mm, noise 1.5-3 grey levels) give 0.00019 .. 0.0015. The limit is set at the geometric
 * middle between the blurriest fixture (sigma 0.27 mm, 0.00019) and sigma 4 px = 0.35 mm (0.00011), i.e. photos blurrier than about a
 * 0.3 mm Gaussian are refused. TO MEASURE on real phone photos (autofocus, motion blur, JPEG): which blur still gives a 0.1 mm rim.
 */
export const MIN_SHARPNESS = 0.00015;
/**
 * Fallback for photos in which the reference is not found or does not fit (NO_REFERENCE, REFERENCE_TILTED): above this edgeWidthPx
 * the whole photo is blurred and the error is BLURRY, because blur is then the real cause (the markers cannot be read through it).
 * Scale: photo shrunk to 1600 px wide, i.e. about 5.5 photo px/mm with the sheet filling the frame. Derivation, from this repo's
 * synthetic runs only: rig fixtures (blur 0.7-1.5 px, noise up to 3) give 3.5 .. 5.1; the same fixtures blurred by a further
 * sigma of 2 / 3 / 4 / 6 px give 6.4-7.2 / 8.0-8.9 / 9.5-10.7 / 12.5-14.2, at which detection no longer works. The limit sits
 * between the sharp fixtures and the sigma 3 px ones, about 0.5 mm of Gaussian blur at that scale. TO MEASURE on real phone photos.
 */
export const MAX_EDGE_WIDTH_PX = 7.5;
const FLAT_FRACTION = 0.15; // local range, as a share of the patch contrast, under which a pixel counts as flat
const MIN_FLAT_SHARE = 0.02; // share of flat pixels needed to trust the noise estimate
const SHARPNESS_MARGIN_MM = 1; // paper around the marker square, so its outer edge is inside the patch

const DETECT_WIDTH = 1600;
const EDGE_QUANTILE = 0.995;
const MIN_MARKERS = 4;
const MIN_INLIERS = 8;
const INLIER_MM = 1; // a corner further than this from the fit is an outlier (misread marker); the 0.3 mm rule applies to the inliers
const DEFAULT_FOCAL35MM = 26; // only used to estimate the tilt when the photo has no focal length; TO MEASURE per phone

export interface Reference {
  H: number[];            // board mm -> photo px, 9 numbers row-major
  reprojErrMm: number;
  tiltDeg: number;
  cameraDistMm?: number;  // camera to window centre, only when photo.focal35mm is known
  nMarkers: number;
  markerIds: number[];    // markers whose corners are inliers of the fit
}

function toGrey(img: ImageData): Uint8Array {
  const d = img.data, g = new Uint8Array(img.width * img.height);
  for (let i = 0, j = 0; i < g.length; i++, j += 4) g[i] = (77 * d[j] + 150 * d[j + 1] + 29 * d[j + 2]) >> 8;
  return g;
}

function bilinear(g: Uint8Array, w: number, h: number, x: number, y: number): number {
  const xc = Math.min(Math.max(x, 0), w - 1.001), yc = Math.min(Math.max(y, 0), h - 1.001);
  const x0 = Math.floor(xc), y0 = Math.floor(yc), fx = xc - x0, fy = yc - y0, i = y0 * w + x0;
  return (g[i] * (1 - fx) + g[i + 1] * fx) * (1 - fy) + (g[i + w] * (1 - fx) + g[i + w + 1] * fx) * fy;
}

/**
 * Sub-pixel corners at full resolution. OpenCV.js here has no cornerSubPix, so each marker side is located by
 * the steepest edge along 16 normals, a line is fitted per side, and adjacent lines are intersected.
 * Returns the input quad when a side cannot be fitted.
 */
function refineQuad(g: Uint8Array, w: number, h: number, quad: Pt[], reach: number): Pt[] {
  const cx = quad.reduce((s, p) => s + p[0], 0) / 4, cy = quad.reduce((s, p) => s + p[1], 0) / 4;
  const lines: { m: Pt; d: Pt }[] = [];
  const STEP = 0.5, K = 16;
  for (let i = 0; i < 4; i++) {
    const a = quad[i], b = quad[(i + 1) % 4];
    const ex = b[0] - a[0], ey = b[1] - a[1], len = Math.hypot(ex, ey);
    if (len < 24) return quad;
    let nx = ey / len, ny = -ex / len;
    if (nx * ((a[0] + b[0]) / 2 - cx) + ny * ((a[1] + b[1]) / 2 - cy) < 0) { nx = -nx; ny = -ny; }
    const n = Math.round((2 * reach) / STEP) + 1;
    const pts: Pt[] = [];
    for (let k = 0; k < K; k++) {
      const f = 0.2 + (0.6 * k) / (K - 1), sx = a[0] + ex * f, sy = a[1] + ey * f;
      const grad: number[] = [];
      for (let j = 0; j < n; j++) {
        const t = -reach + j * STEP;
        grad.push(bilinear(g, w, h, sx + nx * (t + STEP / 2), sy + ny * (t + STEP / 2)) - bilinear(g, w, h, sx + nx * (t - STEP / 2), sy + ny * (t - STEP / 2)));
      }
      let jm = 1;
      for (let j = 1; j < n - 1; j++) if (grad[j] > grad[jm]) jm = j;
      if (grad[jm] < 15 || jm === n - 1) continue; // inside is dark, outside is light: expect a rising edge
      const den = grad[jm - 1] - 2 * grad[jm] + grad[jm + 1];
      const t = -reach + jm * STEP + (den < 0 ? 0.5 * ((grad[jm - 1] - grad[jm + 1]) / den) * STEP : 0);
      pts.push([sx + nx * t, sy + ny * t]);
    }
    const line = fitLine(pts);
    if (!line) return quad;
    lines.push(line);
  }
  const out: Pt[] = [];
  for (let i = 0; i < 4; i++) {
    const l1 = lines[(i + 3) % 4], l2 = lines[i];
    const cr = l1.d[0] * l2.d[1] - l1.d[1] * l2.d[0];
    if (Math.abs(cr) < 0.3) return quad;
    const t = ((l2.m[0] - l1.m[0]) * l2.d[1] - (l2.m[1] - l1.m[1]) * l2.d[0]) / cr;
    const p: Pt = [l1.m[0] + l1.d[0] * t, l1.m[1] + l1.d[1] * t];
    if (Math.hypot(p[0] - quad[i][0], p[1] - quad[i][1]) > reach + 2) return quad;
    out.push(p);
  }
  return out;
}

function fitLine(pts: Pt[]): { m: Pt; d: Pt } | null {
  let use = pts;
  for (let pass = 0; pass < 2; pass++) {
    if (use.length < 6) return null;
    const mx = use.reduce((s, p) => s + p[0], 0) / use.length, my = use.reduce((s, p) => s + p[1], 0) / use.length;
    let sxx = 0, sxy = 0, syy = 0;
    for (const p of use) { sxx += (p[0] - mx) ** 2; sxy += (p[0] - mx) * (p[1] - my); syy += (p[1] - my) ** 2; }
    const th = 0.5 * Math.atan2(2 * sxy, sxx - syy), d: Pt = [Math.cos(th), Math.sin(th)];
    const res = use.map((p) => (p[0] - mx) * -d[1] + (p[1] - my) * d[0]);
    const rms = Math.sqrt(res.reduce((s, r) => s + r * r, 0) / use.length);
    if (pass === 1 || rms < 0.2) return { m: [mx, my], d };
    use = use.filter((_, i) => Math.abs(res[i]) <= Math.max(0.4, 2.5 * rms));
  }
  return null;
}

/** Marker corners in photo px (full resolution), by id. Ids seen twice are dropped. */
function detectMarkers(cv: Cv, grey: Uint8Array, w: number, h: number, spec: BoardSpec): Map<number, Pt[]> {
  const dictId = (cv as unknown as Record<string, unknown>)[spec.dictionary];
  if (typeof dictId !== 'number') throw new OptiError('LOAD_FAILED', 'unknown dictionary ' + spec.dictionary);
  const trash: { delete(): void }[] = [];
  const keep = <T extends { delete(): void }>(o: T): T => (trash.push(o), o);
  try {
    const full = keep(new cv.Mat(h, w, cv.CV_8UC1));
    full.data.set(grey);
    let small = full;
    if (w > DETECT_WIDTH) {
      small = keep(new cv.Mat());
      cv.resize(full, small, new cv.Size(DETECT_WIDTH, Math.round((h * DETECT_WIDTH) / w)), 0, 0, cv.INTER_AREA);
    }
    const sx = small.cols / w, sy = small.rows / h;
    const detector = keep(new cv.aruco_ArucoDetector(keep(cv.getPredefinedDictionary(dictId)), keep(new cv.aruco_DetectorParameters()), keep(new cv.aruco_RefineParameters(10, 3, true))));
    const corners = keep(new cv.MatVector()), ids = keep(new cv.Mat()), rejected = keep(new cv.MatVector());
    detector.detectMarkers(small, corners, ids, rejected);
    const found = new Map<number, Pt[]>();
    const dup = new Set<number>();
    const reach = 2 / Math.min(sx, sy) + 3; // detection error at the small scale, plus the 0.5 px threshold bias
    for (let i = 0; i < corners.size(); i++) { // ids is 1 x N in this build, so rows is not the count
      const id = ids.data32S[i];
      if (found.has(id)) { dup.add(id); continue; }
      const c = keep(corners.get(i)).data32F;
      const quad: Pt[] = [0, 1, 2, 3].map((k) => [(c[2 * k] + 0.5) / sx - 0.5, (c[2 * k + 1] + 0.5) / sy - 0.5]);
      found.set(id, refineQuad(grey, w, h, quad, reach));
    }
    for (const id of dup) found.delete(id);
    return found;
  } finally {
    for (const o of trash) o.delete();
  }
}

/** Camera pose of the board plane from H (board mm -> px) and intrinsics (f, principal point at the image centre). */
function planePose(H: Mat3, fPx: number, cx: number, cy: number, centre: Pt): { tiltDeg: number; distMm: number } | null {
  const m = [(H[0] - cx * H[6]) / fPx, (H[1] - cx * H[7]) / fPx, (H[2] - cx * H[8]) / fPx,
    (H[3] - cy * H[6]) / fPx, (H[4] - cy * H[7]) / fPx, (H[5] - cy * H[8]) / fPx, H[6], H[7], H[8]];
  const c1 = [m[0], m[3], m[6]], c2 = [m[1], m[4], m[7]], c3 = [m[2], m[5], m[8]];
  let lambda = 2 / (Math.hypot(...c1) + Math.hypot(...c2));
  const p = [0, 1, 2].map((k) => lambda * (c1[k] * centre[0] + c2[k] * centre[1] + c3[k]));
  if (p[2] < 0) { lambda = -lambda; p.forEach((_, k) => (p[k] = -p[k])); }
  const r1 = c1.map((v) => v * lambda), r2 = c2.map((v) => v * lambda);
  const nz = r1[0] * r2[1] - r1[1] * r2[0]; // z component of r1 x r2
  const nn = Math.hypot(r1[1] * r2[2] - r1[2] * r2[1], r1[2] * r2[0] - r1[0] * r2[2], nz);
  const tiltDeg = (Math.acos(Math.min(1, Math.abs(nz) / nn)) * 180) / Math.PI;
  const distMm = Math.hypot(...p);
  return Number.isFinite(tiltDeg) && Number.isFinite(distMm) ? { tiltDeg, distMm } : null;
}

/** Markers, homography, quality checks. Throws NO_REFERENCE or REFERENCE_TILTED. */
export async function locateReference(photo: Photo, spec: BoardSpec): Promise<Reference> {
  const cv = await timedAsync('opencv-load', loadOpenCv);
  const { width: w, height: h } = photo.image;
  // Detection runs on a copy shrunk to DETECT_WIDTH; only the corner refinement reads the full-resolution grey image.
  const found = timed('detect', () => detectMarkers(cv, toGrey(photo.image), w, h, spec));
  const ps = spec.printScale;
  const img: Pt[] = [], board: Pt[] = [], owner: number[] = [];
  for (const m of spec.markers) {
    const q = found.get(m.id);
    if (!q) continue;
    for (let k = 0; k < 4; k++) { img.push(q[k]); board.push([m.corners[k][0] * ps, m.corners[k][1] * ps]); owner.push(m.id); }
  }
  const matched = new Set(owner).size;
  if (matched < MIN_MARKERS) throw new OptiError('NO_REFERENCE', `${matched} of ${MIN_MARKERS} markers`);

  // Fit photo px -> board mm so that the residual and the inlier test are in mm.
  const fit = ransacHomography(img, board, { threshold: INLIER_MM, minInliers: MIN_INLIERS });
  const inlierMarkers = fit ? new Set(owner.filter((_, i) => fit.inliers[i])).size : 0;
  if (!fit || inlierMarkers < MIN_MARKERS) throw new OptiError('REFERENCE_TILTED', 'marker corners do not fit one plane');
  const H = invert3(fit.H);
  if (!H) throw new OptiError('REFERENCE_TILTED', 'degenerate homography');
  if (fit.rms > MAX_REPROJ_MM) throw new OptiError('REFERENCE_TILTED', `reproj ${fit.rms.toFixed(2)} mm > ${MAX_REPROJ_MM} mm`);

  const f35 = photo.focal35mm && photo.focal35mm > 0 ? photo.focal35mm : undefined;
  // 35 mm equivalent focal length refers to the long side of the frame.
  const fPx = ((f35 ?? DEFAULT_FOCAL35MM) / 36) * Math.max(w, h);
  const centre: Pt = [(spec.windowMm.w * ps) / 2, (spec.windowMm.h * ps) / 2];
  const pose = planePose(H, fPx, w / 2, h / 2, centre);
  if (pose && pose.tiltDeg > MAX_TILT_DEG) throw new OptiError('REFERENCE_TILTED', `tilt ${pose.tiltDeg.toFixed(0)} deg > ${MAX_TILT_DEG} deg`);
  const markerIds = [...new Set(owner.filter((_, i) => fit.inliers[i]))];
  return { H, reprojErrMm: fit.rms, tiltDeg: pose?.tiltDeg ?? 0, cameraDistMm: f35 && pose ? pose.distMm : undefined, nMarkers: inlierMarkers, markerIds };
}

/**
 * Contrast-normalised edge sharpness of one grey patch: variance of the 4-neighbour Laplacian (interior pixels)
 * divided by the squared 5th-95th percentile spread of the patch, so that paper and ink levels, exposure and
 * printer density cancel. Sensor noise also feeds the Laplacian, so its share is removed: the noise level is the
 * mean square Laplacian over the flat pixels (5 x 5 neighbourhood range below FLAT_FRACTION of the spread), where
 * only noise is present, and it is subtracted from the variance. 0 for a flat patch, for a noise-only patch and
 * for a patch without enough flat pixels to measure noise (very blurred or very noisy).
 */
export function patchSharpness(g: Uint8Array, w: number, h: number): number {
  const hist = new Uint32Array(256);
  for (let i = 0; i < g.length; i++) hist[g[i]]++;
  const at = (q: number) => { let c = 0; for (let v = 0; v < 256; v++) { c += hist[v]; if (c >= q * g.length) return v; } return 255; };
  const spread = at(0.95) - at(0.05);
  if (spread < 20 || w < 7 || h < 7) return 0; // no marker structure left in the patch (flat or covered)
  const flatMax = FLAT_FRACTION * spread;
  let sum = 0, sum2 = 0, n = 0, fSum2 = 0, fN = 0;
  for (let y = 2; y < h - 2; y++) {
    for (let x = 2; x < w - 2; x++) {
      const i = y * w + x, l = g[i - 1] + g[i + 1] + g[i - w] + g[i + w] - 4 * g[i];
      sum += l; sum2 += l * l; n++;
      let lo = 255, hi = 0;
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { const v = g[i + dy * w + dx]; if (v < lo) lo = v; if (v > hi) hi = v; }
      if (hi - lo <= flatMax) { fSum2 += l * l; fN++; }
    }
  }
  if (fN < MIN_FLAT_SHARE * n) return 0;
  const mean = sum / n;
  return Math.max(0, sum2 / n - mean * mean - fSum2 / fN) / (spread * spread);
}

/**
 * Sharpness of the photo, measured on the reference markers and not on the window, so that it does not depend on
 * what lies in the window (an empty window, a faint lens rim, a noisy background). Each marker square plus a margin is
 * warped to a 10 px/mm patch like the window; the figure is the median of patchSharpness over the markers, which
 * tolerates one or two covered markers. Higher is sharper. Throws NO_REFERENCE if no marker patch can be warped.
 */
export function referenceSharpness(cv: Cv, src: ImageData, spec: BoardSpec, H: Mat3, markerIds: number[]): number {
  const ps = spec.printScale, vals: number[] = [];
  for (const id of markerIds) {
    const m = spec.markers.find((k) => k.id === id);
    if (!m) continue;
    const xs = m.corners.map((c) => c[0] * ps), ys = m.corners.map((c) => c[1] * ps);
    const x0 = Math.min(...xs) - SHARPNESS_MARGIN_MM, y0 = Math.min(...ys) - SHARPNESS_MARGIN_MM;
    let patch: ImageData;
    try { patch = warpRegion(cv, src, H, x0, y0, Math.max(...xs) - Math.min(...xs) + 2 * SHARPNESS_MARGIN_MM, Math.max(...ys) - Math.min(...ys) + 2 * SHARPNESS_MARGIN_MM); } catch (e) {
      if (e instanceof OptiError) continue; // marker too close to the photo edge: skip it
      throw e;
    }
    vals.push(patchSharpness(toGrey(patch), patch.width, patch.height));
  }
  if (vals.length === 0) throw new OptiError('NO_REFERENCE', 'no marker patch inside the photo');
  vals.sort((a, b) => a - b);
  const mid = vals.length >> 1;
  return vals.length % 2 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
}

/**
 * Width in photo px (of the photo shrunk to DETECT_WIDTH) of the steepest edges: contrast divided by the 99.5th percentile of the
 * gradient magnitude, after a [1 2 1] smoothing that keeps sensor noise out of the gradient. About 2.5 x the Gaussian sigma of an
 * edge. 0 when the photo has no structure (flat or covered): then nothing can be said and it is not called blurred.
 * Needs no marker, so it also judges photos in which the reference was not found.
 */
export function edgeWidthPx(cv: Cv, img: ImageData): number {
  const grey = toGrey(img);
  let g = grey, w = img.width, h = img.height;
  if (w > DETECT_WIDTH) {
    const full = new cv.Mat(h, w, cv.CV_8UC1), small = new cv.Mat();
    try {
      full.data.set(grey);
      cv.resize(full, small, new cv.Size(DETECT_WIDTH, Math.round((h * DETECT_WIDTH) / w)), 0, 0, cv.INTER_AREA);
      g = new Uint8Array(small.data); w = small.cols; h = small.rows;
    } finally { full.delete(); small.delete(); }
  }
  if (w < 8 || h < 8) return 0;
  const tmp = new Float32Array(w * h), sm = new Float32Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 1; x < w - 1; x++) tmp[y * w + x] = (g[y * w + x - 1] + 2 * g[y * w + x] + g[y * w + x + 1]) / 4;
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) sm[y * w + x] = (tmp[(y - 1) * w + x] + 2 * tmp[y * w + x] + tmp[(y + 1) * w + x]) / 4;
  const GRAD_BIN = 0.25, gh = new Uint32Array(2048), ih = new Uint32Array(256);
  let n = 0;
  for (let y = 2; y < h - 2; y++) {
    for (let x = 2; x < w - 2; x++) {
      const i = y * w + x;
      ih[Math.round(sm[i])]++;
      gh[Math.min(2047, Math.floor(Math.hypot(sm[i + 1] - sm[i - 1], sm[i + w] - sm[i - w]) / 2 / GRAD_BIN))]++;
      n++;
    }
  }
  const quantile = (hist: Uint32Array, q: number) => { let c = 0; for (let v = 0; v < hist.length; v++) { c += hist[v]; if (c >= q * n) return v; } return hist.length - 1; };
  const spread = quantile(ih, 0.98) - quantile(ih, 0.02);
  const grad = (quantile(gh, EDGE_QUANTILE) + 1) * GRAD_BIN;
  return spread < 20 ? 0 : spread / grad;
}

/** Top view of the window at PX_PER_MM, with the reprojection error and sharpness. */
export async function rectify(photo: Photo, spec: BoardSpec): Promise<Rectified> {
  try {
    const ref = await locateReference(photo, spec);
    const cv = await loadOpenCv();
    const image = timed('warp', () => warpWindow(cv, photo.image, spec, ref.H)); // the only warp of the window, straight to PX_PER_MM
    const sharpness = timed('sharpness', () => referenceSharpness(cv, photo.image, spec, ref.H, ref.markerIds));
    if (sharpness < MIN_SHARPNESS) throw new OptiError('BLURRY', `sharpness ${sharpness.toFixed(5)} < ${MIN_SHARPNESS}`);
    return { image, pxPerMm: PX_PER_MM, H: ref.H, reprojErrMm: ref.reprojErrMm, sharpness, cameraDistMm: ref.cameraDistMm };
  } catch (e) {
    if (e instanceof OptiError && (e.code === 'NO_REFERENCE' || e.code === 'REFERENCE_TILTED')) {
      // A heavily blurred photo loses its markers first: report the cause, not the symptom.
      let width = 0;
      try { width = edgeWidthPx(await loadOpenCv(), photo.image); } catch { /* keep the original error */ }
      if (width > MAX_EDGE_WIDTH_PX) throw new OptiError('BLURRY', `edges ${width.toFixed(1)} px > ${MAX_EDGE_WIDTH_PX} px (${e.message})`);
    }
    if (e instanceof OptiError) throw e;
    throw new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e)); // rule: only OptiError leaves this module
  }
}

function warpWindow(cv: Cv, src: ImageData, spec: BoardSpec, H: Mat3): ImageData {
  return warpRegion(cv, src, H, 0, 0, spec.windowMm.w, spec.windowMm.h);
}

/** Top view of the board rectangle [x0, x0+ww] x [y0, y0+wh] (physical mm) at PX_PER_MM. */
function warpRegion(cv: Cv, src: ImageData, H: Mat3, x0: number, y0: number, ww: number, wh: number): ImageData {
  const outW = Math.round(ww * PX_PER_MM), outH = Math.round(wh * PX_PER_MM);
  // Region outline in the photo, to crop the source and decide how much to shrink it first.
  const quad = ([[x0, y0], [x0 + ww, y0], [x0 + ww, y0 + wh], [x0, y0 + wh]] as Pt[]).map((p) => applyH(H, p));
  const side = (a: Pt, b: Pt) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const density = (side(quad[0], quad[1]) / ww + side(quad[3], quad[2]) / ww + side(quad[0], quad[3]) / wh + side(quad[1], quad[2]) / wh) / 4; // photo px per mm
  // Lanczos only interpolates: average the source down by an integer factor first when it is much denser than 10 px/mm.
  const k = Math.max(1, Math.floor(density / PX_PER_MM + 1e-6));
  const margin = 6 * k;
  const ox = Math.max(0, Math.floor(Math.min(...quad.map((p) => p[0])) - margin)), oy = Math.max(0, Math.floor(Math.min(...quad.map((p) => p[1])) - margin));
  const ex = Math.min(src.width, Math.ceil(Math.max(...quad.map((p) => p[0])) + margin)), ey = Math.min(src.height, Math.ceil(Math.max(...quad.map((p) => p[1])) + margin));
  const rw = Math.floor((ex - ox) / k) * k, rh = Math.floor((ey - oy) / k) * k;
  if (rw < 8 * k || rh < 8 * k) throw new OptiError('NO_REFERENCE', 'region outside the photo');

  const trash: { delete(): void }[] = [];
  const keep = <T extends { delete(): void }>(o: T): T => (trash.push(o), o);
  try {
    const crop = keep(new cv.Mat(rh, rw, cv.CV_8UC4));
    for (let y = 0; y < rh; y++) crop.data.set(src.data.subarray(((oy + y) * src.width + ox) * 4, ((oy + y) * src.width + ox + rw) * 4), y * rw * 4);
    let input = crop;
    if (k > 1) {
      input = keep(new cv.Mat());
      cv.resize(crop, input, new cv.Size(rw / k, rh / k), 0, 0, cv.INTER_AREA);
    }
    // dst pixel -> mm -> photo px -> crop px -> shrunk px (all centre-at-integer except mm, see header)
    const toMm: Mat3 = [1 / PX_PER_MM, 0, x0 + 0.5 / PX_PER_MM, 0, 1 / PX_PER_MM, y0 + 0.5 / PX_PER_MM, 0, 0, 1];
    const toCrop: Mat3 = [1 / k, 0, (0.5 - ox) / k - 0.5, 0, 1 / k, (0.5 - oy) / k - 0.5, 0, 0, 1];
    const M = keep(cv.matFromArray(3, 3, cv.CV_64F, mul3(toCrop, mul3(H, toMm))));
    const dst = keep(new cv.Mat());
    cv.warpPerspective(input, dst, M, new cv.Size(outW, outH), cv.INTER_LANCZOS4 | cv.WARP_INVERSE_MAP, cv.BORDER_REPLICATE, new cv.Scalar());
    return new ImageData(new Uint8ClampedArray(dst.data), outW, outH);
  } finally {
    for (const o of trash) o.delete();
  }
}
