import { readFileSync } from 'node:fs';
import { beforeAll, describe, expect, it } from 'vitest';
import { OptiError, PX_PER_MM, type BoardSpec } from '../contracts';
import { applyH, type Mat3 } from './homography';
import { evalOpenCv, loadOpenCv } from './opencv';
import { MAX_REPROJ_MM, MIN_SHARPNESS, locateReference, patchSharpness, rectify, referenceSharpness } from './rectify';
import { INK, PAPER, defaultSpec, renderScene, type BoardCanvas, type Scene } from './rectify.testutil';

const T = 180_000;

async function code(p: Promise<unknown>): Promise<string> {
  try { await p; } catch (e) { if (e instanceof OptiError) return e.message; throw e; }
  return 'no error';
}

// Board drawings are in nominal mm, physical mm = nominal * printScale, hence the division.
function bars(spec: BoardSpec) {
  const s = spec.printScale;
  return (c: BoardCanvas) => {
    c.rect(10 / s, 29.5 / s, 60 / s, 30.5 / s, INK);     // horizontal, 50.0 mm physical
    c.rect(69.5 / s, 10 / s, 70.5 / s, 50 / s, INK);     // vertical, 40.0 mm physical
  };
}

/** Length of a dark bar, integrated over a band of rows (or columns) so that edge blur and sub-pixel ends count. */
function barLengthMm(img: ImageData, horizontal: boolean, centreMm: number, fromMm: number, toMm: number): number {
  const { width: w, height: h, data } = img;
  const lines = [-2, -1, 0, 1].map((o) => Math.floor(centreMm * PX_PER_MM) + o); // pixels covering centre +- 0.2 mm
  const n = horizontal ? w : h;
  let sum = 0;
  for (const l of lines) {
    for (let i = Math.floor(fromMm * PX_PER_MM); i < Math.min(n, Math.ceil(toMm * PX_PER_MM)); i++) {
      const v = horizontal ? data[(l * w + i) * 4] : data[(i * w + l) * 4];
      sum += (PAPER - v) / (PAPER - INK); // no clamp: noise must average out
    }
  }
  return sum / lines.length / PX_PER_MM;
}

describe('opencv loader', () => {
  it('exposes the ArUco API used here and loads once', async () => {
    const cv = await loadOpenCv();
    expect(await loadOpenCv()).toBe(cv);
    for (const n of ['aruco_ArucoDetector', 'aruco_DetectorParameters', 'aruco_RefineParameters', 'getPredefinedDictionary', 'generateImageMarker', 'DICT_4X4_50', 'warpPerspective', 'INTER_LANCZOS4', 'resize']) {
      expect((cv as unknown as Record<string, unknown>)[n], n).toBeDefined();
    }
    expect((cv as unknown as Record<string, unknown>).cornerSubPix).toBeUndefined(); // hence the own refinement in rectify.ts
  }, T);

  it('browser path: the vendored file runs through evalOpenCv without a script tag', async () => {
    const text = readFileSync(new URL('../../public/vendor/opencv/opencv.js', import.meta.url), 'utf8');
    // The build picks its environment from globalThis.process: hide it while the factory runs so Node behaves like a page.
    const realProcess = Object.getOwnPropertyDescriptor(globalThis, 'process')!;
    let raw: unknown;
    try {
      Object.defineProperty(globalThis, 'process', { value: undefined, configurable: true, writable: true });
      raw = evalOpenCv(text);
    } finally {
      Object.defineProperty(globalThis, 'process', realProcess);
    }
    const cv = (await raw) as { Mat?: unknown; aruco_ArucoDetector?: unknown };
    expect(cv.Mat).toBeDefined();
    expect(cv.aruco_ArucoDetector).toBeDefined();
  }, T);
});

describe('rectify on synthetic scenes', () => {
  const spec = defaultSpec();
  let frontal: Scene;
  beforeAll(async () => { frontal = await renderScene(spec, { draw: bars(spec) }); }, T);

  it('measures a 50.0 mm and a 40.0 mm segment within 0.1 mm, frontal view', async () => {
    const r = await rectify(frontal.photo, spec);
    expect(r.image.width).toBe(800);
    expect(r.image.height).toBe(650);
    expect(r.pxPerMm).toBe(PX_PER_MM);
    expect(r.reprojErrMm).toBeLessThan(0.1);
    console.log(`frontal: 50 mm bar reads ${barLengthMm(r.image, true, 30, 5, 65).toFixed(3)}, 40 mm bar reads ${barLengthMm(r.image, false, 70, 5, 55).toFixed(3)}, reproj ${r.reprojErrMm.toFixed(3)} mm`);
    expect(Math.abs(barLengthMm(r.image, true, 30, 5, 65) - 50)).toBeLessThan(0.1);
    expect(Math.abs(barLengthMm(r.image, false, 70, 5, 55) - 40)).toBeLessThan(0.1);
  }, T);

  it('measures within 0.1 mm with a tilted, rolled, off-axis and noisy camera', async () => {
    const s = await renderScene(spec, { tiltDeg: 22, panDeg: -12, rollDeg: 17, shiftMm: [14, -9], distMm: 230, noiseSigma: 2, draw: bars(spec) });
    const r = await rectify(s.photo, spec);
    console.log(`tilted: 50 mm bar reads ${barLengthMm(r.image, true, 30, 5, 65).toFixed(3)}, 40 mm bar reads ${barLengthMm(r.image, false, 70, 5, 55).toFixed(3)}, reproj ${r.reprojErrMm.toFixed(3)} mm`);
    expect(Math.abs(barLengthMm(r.image, true, 30, 5, 65) - 50)).toBeLessThan(0.1);
    expect(Math.abs(barLengthMm(r.image, false, 70, 5, 55) - 40)).toBeLessThan(0.1);
    // The fitted H lands within half a photo pixel of the true one over the window.
    for (const p of [[0, 0], [80, 0], [80, 65], [0, 65], [40, 32]] as [number, number][]) {
      const a = applyH(r.H, p), b = applyH(s.Htrue, p);
      expect(Math.hypot(a[0] - b[0], a[1] - b[1])).toBeLessThan(0.5);
    }
  }, T);

  it('uses printScale: a sheet printed at 99 % still measures true millimetres', async () => {
    const spec99 = defaultSpec(0.99);
    const s = await renderScene(spec99, { draw: bars(spec99) });
    const r = await rectify(s.photo, spec99);
    expect(Math.abs(barLengthMm(r.image, true, 30, 5, 65) - 50)).toBeLessThan(0.1);
    // With printScale ignored the same photo would read about 49.5 mm: make sure the test can tell.
    const r1 = await rectify(s.photo, { ...spec99, printScale: 1 });
    expect(Math.abs(barLengthMm(r1.image, true, 30, 5, 65) - 50)).toBeGreaterThan(0.3);
  }, T);

  it('shrinks a very dense photo before the Lanczos warp and still measures within 0.1 mm', async () => {
    // about 30 px/mm in the photo: shrink factor 3
    const s = await renderScene(spec, { width: 6000, height: 4500, supersample: 1, distMm: 130, f35: 26, draw: bars(spec) });
    const r = await rectify(s.photo, spec);
    console.log(`dense: 50 mm bar reads ${barLengthMm(r.image, true, 30, 5, 65).toFixed(3)}`);
    expect(Math.abs(barLengthMm(r.image, true, 30, 5, 65) - 50)).toBeLessThan(0.1);
  }, T);

  it('reports cameraDistMm within 3 % of the true distance when focal35mm is known', async () => {
    for (const o of [{ distMm: 200, tiltDeg: 0 }, { distMm: 260, tiltDeg: 15, panDeg: 8, f35: 24 }, { distMm: 320, tiltDeg: -20, rollDeg: 30, shiftMm: [20, 10] as [number, number], f35: 28 }]) {
      const s = await renderScene(spec, { ...o, draw: bars(spec) });
      const ref = await locateReference(s.photo, spec);
      const err = Math.abs(ref.cameraDistMm! / s.trueDistMm - 1);
      console.log(`pose ${JSON.stringify(o)}: ${ref.cameraDistMm?.toFixed(1)} mm vs ${s.trueDistMm.toFixed(1)} mm (${(err * 100).toFixed(2)} %), tilt est ${ref.tiltDeg.toFixed(1)} deg`);
      expect(ref.cameraDistMm).toBeDefined();
      expect(err).toBeLessThan(0.03);
    }
  }, T);

  it('leaves cameraDistMm undefined without a focal length', async () => {
    const r = await rectify({ ...frontal.photo, focal35mm: undefined }, spec);
    expect(r.cameraDistMm).toBeUndefined();
  }, T);

  it('NO_REFERENCE: fewer than 4 markers, and an empty photo', async () => {
    const few = { ...spec, markers: spec.markers.slice(0, 3) };
    const s = await renderScene(few, { draw: bars(spec) });
    expect(await code(rectify(s.photo, spec))).toMatch(/^NO_REFERENCE/);
    const blank = new ImageData(new Uint8ClampedArray(640 * 480 * 4).fill(128), 640, 480);
    expect(await code(rectify({ image: blank, source: 'file' }, spec))).toMatch(/^NO_REFERENCE/);
  }, T);

  it('REFERENCE_TILTED: plane tilted by more than 35 degrees', async () => {
    const s = await renderScene(spec, { tiltDeg: 50, distMm: 260, draw: bars(spec) });
    expect(await code(rectify(s.photo, spec))).toMatch(/^REFERENCE_TILTED: tilt/);
  }, T);

  it('REFERENCE_TILTED: marker corners that do not lie on one plane (lens or paper warp), residual above the limit', async () => {
    const s = await renderScene(spec, { width: 1600, height: 1200, radialK: 0.15, draw: bars(spec) });
    expect(await code(rectify(s.photo, spec))).toMatch(/^REFERENCE_TILTED: reproj/);
    expect(MAX_REPROJ_MM).toBe(0.3);
  }, T);

  it('BLURRY, not NO_REFERENCE: a photo blurred so much that no marker is read (dense 3200 px scene, sigma 10 px)', async () => {
    const s = await renderScene(spec, { blurSigma: 10, noiseSigma: 3, draw: bars(spec) });
    const msg = await code(rectify(s.photo, spec));
    console.log(`blurred beyond detection: ${msg}`);
    expect(msg).toMatch(/^BLURRY: edges/);
  }, T);

  it('BLURRY: markers are found but the reference sharpness is below MIN_SHARPNESS', async () => {
    const sharp = await rectify(frontal.photo, spec);
    const s = await renderScene(spec, { blurSigma: 6, draw: bars(spec) });
    const msg = await code(rectify(s.photo, spec));
    console.log(`sharpness sharp=${sharp.sharpness.toFixed(5)}, blurred: ${msg}, MIN_SHARPNESS=${MIN_SHARPNESS}`);
    expect(sharp.sharpness).toBeGreaterThan(MIN_SHARPNESS);
    expect(msg).toMatch(/^BLURRY/);
  }, T);
});

describe('Rectified.sharpness is measured on the reference markers', () => {
  const spec = defaultSpec();
  const lens = (c: BoardCanvas) => { // a lens with a faint rim, as on the real sheet
    c.rect(15, 12, 65, 52, 200);
    c.rect(16, 13, 64, 51, PAPER);
  };
  const ids = spec.markers.map((m) => m.id);
  async function sharpnessOf(s: Scene): Promise<number> {
    const cv = await loadOpenCv();
    const ref = await locateReference(s.photo, spec);
    return referenceSharpness(cv, s.photo.image, spec, ref.H as Mat3, ref.markerIds);
  }

  it('is the same for an empty window and a window holding a lens (within 5 %)', async () => {
    const empty = await renderScene(spec, { tiltDeg: 10, noiseSigma: 1.5 });
    const full = await renderScene(spec, { tiltDeg: 10, noiseSigma: 1.5, draw: lens });
    const a = await rectify(empty.photo, spec), b = await rectify(full.photo, spec); // both ACCEPTED
    console.log(`empty window ${a.sharpness.toFixed(5)}, lens in window ${b.sharpness.toFixed(5)}`);
    expect(Math.abs(b.sharpness / a.sharpness - 1)).toBeLessThan(0.05);
    expect(a.sharpness).toBeGreaterThan(MIN_SHARPNESS);
  }, T);

  it('blur sweep: sigma 0, 1, 2, 3, 4, 6 px decreases strictly; 0..3 accepted, 4 and 6 are BLURRY', async () => {
    const values: number[] = [], outcomes: string[] = [];
    for (const sigma of [0, 1, 2, 3, 4, 6]) {
      const s = await renderScene(spec, { blurSigma: sigma, draw: bars(spec) });
      values.push(await sharpnessOf(s));
      outcomes.push((await code(rectify(s.photo, spec))).replace(/ .*/, ''));
    }
    console.log(`blur sweep sigma 0,1,2,3,4,6 px: ${values.map((v) => v.toFixed(5)).join(' ')}; MIN_SHARPNESS=${MIN_SHARPNESS}; ${outcomes.join(' | ')}`);
    for (let i = 1; i < values.length; i++) expect(values[i]).toBeLessThan(values[i - 1]);
    expect(outcomes).toEqual(['no', 'no', 'no', 'no', 'BLURRY:', 'BLURRY:']); // 'no error' cut at the first space
    expect(values[3]).toBeGreaterThan(MIN_SHARPNESS);
    expect(values[4]).toBeLessThan(MIN_SHARPNESS);
  }, 6 * T);

  it('sensor noise (sigma 3 grey levels) does not make a heavily blurred photo pass, and barely moves a sharp one', async () => {
    const blurred = await renderScene(spec, { blurSigma: 6, noiseSigma: 3, draw: bars(spec) });
    const clean = await renderScene(spec, { blurSigma: 6, draw: bars(spec) });
    const noisyValue = await sharpnessOf(blurred), cleanValue = await sharpnessOf(clean);
    console.log(`blur 6 px: clean ${cleanValue.toFixed(5)}, noise 3: ${noisyValue.toFixed(5)}`);
    expect(await code(rectify(blurred.photo, spec))).toMatch(/^BLURRY/);
    expect(noisyValue).toBeLessThan(MIN_SHARPNESS);
    const mild = await renderScene(spec, { blurSigma: 2, draw: bars(spec) });
    const mildNoisy = await renderScene(spec, { blurSigma: 2, noiseSigma: 3, draw: bars(spec) });
    const m0 = await sharpnessOf(mild), m3 = await sharpnessOf(mildNoisy);
    console.log(`blur 2 px: clean ${m0.toFixed(5)}, noise 3: ${m3.toFixed(5)}`);
    expect(Math.abs(m3 / m0 - 1)).toBeLessThan(0.1);
    expect((await rectify(mildNoisy.photo, spec)).sharpness).toBeGreaterThan(MIN_SHARPNESS);
  }, 6 * T);

  it('a covered or garbled marker does not break the metric (median over markers)', async () => {
    const cleanScene = await renderScene(spec, { blurSigma: 2, draw: bars(spec) });
    const cv = await loadOpenCv();
    const base = await sharpnessOf(cleanScene);
    const bbox = (id: number) => {
      const m = spec.markers.find((k) => k.id === id)!;
      const q = m.corners.map((c) => applyH(cleanScene.Htrue, c));
      return { x0: Math.floor(Math.min(...q.map((p) => p[0])) - 4), x1: Math.ceil(Math.max(...q.map((p) => p[0])) + 4), y0: Math.floor(Math.min(...q.map((p) => p[1])) - 4), y1: Math.ceil(Math.max(...q.map((p) => p[1])) + 4) };
    };
    // 1. one marker hidden under a flat sticker, another one under a 1 px checkerboard (huge Laplacian): the metric keeps its value.
    const hide = (id: number, fine: boolean) => (g: Uint8Array, w: number) => {
      const b = bbox(id);
      for (let y = b.y0; y < b.y1; y++) for (let x = b.x0; x < b.x1; x++) g[y * w + x] = fine ? ((x + y) & 1 ? 20 : 235) : 128;
    };
    const covered = await renderScene(spec, { blurSigma: 2, draw: bars(spec), occlude: (g, w, h) => { hide(3, false)(g, w); hide(9, true)(g, w); void h; } });
    const withBad = referenceSharpness(cv, covered.photo.image, spec, cleanScene.Htrue as Mat3, ids); // all 14 ids, two of them destroyed
    console.log(`blur 2 px: clean ${base.toFixed(5)}, two markers destroyed (all 14 ids used) ${withBad.toFixed(5)}`);
    expect(Math.abs(withBad / base - 1)).toBeLessThan(0.1);
    // 2. end to end: a hidden marker leaves 13, the photo is still accepted with about the same figure.
    const r = await rectify(covered.photo, spec);
    expect(Math.abs(r.sharpness / base - 1)).toBeLessThan(0.1);
    // 3. a flat patch has no structure, whatever its brightness.
    expect(patchSharpness(new Uint8Array(40 * 40).fill(128), 40, 40)).toBe(0);
  }, 6 * T);
});

describe('timing (desktop, Node, 12 MP photo)', () => {
  it('prints the marker and rectify timings', async () => {
    const spec = defaultSpec();
    const s = await renderScene(spec, { width: 4032, height: 3024, supersample: 1, distMm: 200, f35: 26, draw: bars(spec) });
    await loadOpenCv();
    const t0 = performance.now();
    await locateReference(s.photo, spec);
    const t1 = performance.now();
    const r = await rectify(s.photo, spec);
    const t2 = performance.now();
    console.log(`TIMING desktop 4032x3024: markers+homography ${(t1 - t0).toFixed(0)} ms, full rectify ${(t2 - t1).toFixed(0)} ms (sharpness ${r.sharpness.toFixed(1)}). Phone: TO MEASURE`);
    expect(t2 - t1).toBeLessThan(10_000);
  }, T);
});
