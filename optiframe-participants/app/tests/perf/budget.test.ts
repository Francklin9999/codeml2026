import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { PNG } from 'pngjs';
import { DEFAULT_FRAME, type BoardSpec, type LensMeasurement, type Photo } from '../../src/contracts';
import { meshToStl } from '../../src/export';
import { generateFrame, loadManifold } from '../../src/frame';
import { fuseShots } from '../../src/quality';
import { now } from '../../src/timing';
import { loadOpenCv } from '../../src/vision/opencv';
import { defaultSpec, renderScene } from '../../src/vision/rectify.testutil';
import { handleMessage } from '../../src/worker';

// Regression guard, not a phone figure: in Node on a desktop or a CI runner, everything that runs after OpenCV has
// loaded (rectify, segment, measure for one photo, then fuse of 3 shots, frame generation and STL) must stay under
// BUDGET_MS in total. Phone timings: TO MEASURE, on the "Pas à pas" screen, which shows the same stages.
const BUDGET_MS = 3000;
const STAGES = ['rectify', 'segment', 'measure', 'fuse', 'frame', 'stl'] as const;

const root = new URL('../../../rig/out/', import.meta.url);
const FIXTURE = 'fixtures/fixture_04_ellipse_medium.png';
// BUDGET_SYNTHETIC=1 forces the synthetic photo, to check locally what a CI runner (no rig output) runs.
const hasFixture = !process.env.BUDGET_SYNTHETIC && existsSync(new URL('board_spec.json', root)) && existsSync(new URL(FIXTURE, root));

/** The rig's fixture when it exists (it is not committed); otherwise a synthetic photo of the same size with a dark elliptical rim. */
async function scene(): Promise<{ photo: () => Photo; spec: BoardSpec; name: string }> {
  if (hasFixture) {
    const png = PNG.sync.read(readFileSync(new URL(FIXTURE, root)));
    const spec = JSON.parse(readFileSync(new URL('board_spec.json', root), 'utf8')) as BoardSpec;
    return { photo: () => ({ image: new ImageData(new Uint8ClampedArray(png.data), png.width, png.height), source: 'file' }), spec, name: FIXTURE };
  }
  const spec = defaultSpec();
  const a = 26, b = 21, rim = 2.5, cx = spec.windowMm.w / 2, cy = spec.windowMm.h / 2;
  const s = await renderScene(spec, {
    width: 1600, height: 1200, distMm: 230, tiltDeg: 4,
    draw: ({ rect }) => {
      // Ellipse drawn as thin horizontal spans: a dark band (the rim) around a light inside.
      for (let y = -b; y < b; y += 0.05) {
        const half = a * Math.sqrt(1 - (y / b) ** 2);
        rect(cx - half, cy + y, cx + half, cy + y + 0.05, 30);
        const yi = y / (b - rim);
        if (Math.abs(yi) < 1) { const inner = (a - rim) * Math.sqrt(1 - yi * yi); rect(cx - inner, cy + y, cx + inner, cy + y + 0.05, 225); }
      }
    },
  });
  return { photo: () => ({ ...s.photo, image: new ImageData(new Uint8ClampedArray(s.photo.image.data), s.photo.image.width, s.photo.image.height) }), spec, name: 'synthetic ellipse 1600x1200' };
}

describe('performance budget (Node, regression guard)', () => {
  it(`one photo, fuse, frame and STL take under ${BUDGET_MS} ms after OpenCV has loaded`, async () => {
    const t0 = now();
    await loadOpenCv();
    await loadManifold();
    const loadMs = now() - t0;
    const { photo, spec, name } = await scene();

    const runOnce = async (): Promise<Record<string, number>> => {
      const res = await handleMessage({ type: 'measure', photo: photo(), spec, eye: 'R' });
      if (!res.ok) throw new Error(`${name}: ${res.code}`);
      const t: Record<string, number> = { ...res.timings };
      expect(t['opencv-load'], 'OpenCV was loaded before the run').toBeLessThan(50);
      for (const k of ['rectify', 'detect', 'warp', 'sharpness', 'segment', 'measure', 'worker']) expect(t[k], k).toBeGreaterThanOrEqual(0);
      const shots: LensMeasurement[] = [res.result, res.result, res.result];
      let t1 = now();
      const lens = fuseShots(shots);
      t.fuse = now() - t1;
      t1 = now();
      const frame = await generateFrame({ ...lens, eye: 'L' }, { ...lens, eye: 'R' }, DEFAULT_FRAME);
      t.frame = now() - t1;
      t1 = now();
      const stl = meshToStl(frame);
      t.stl = now() - t1;
      expect(stl.byteLength).toBeGreaterThan(84);
      return t;
    };

    // Two runs, the faster one counts: the first also pays for JIT warm-up, which is not what this guards.
    const runs = [await runOnce(), await runOnce()];
    const total = (t: Record<string, number>) => STAGES.reduce((s, k) => s + t[k], 0);
    const best = runs.reduce((a, b) => (total(b) < total(a) ? b : a));
    console.log(`budget: ${name}; OpenCV + manifold load ${loadMs.toFixed(0)} ms (not counted); `
      + runs.map((t, i) => `run ${i + 1}: ${STAGES.map((k) => `${k} ${t[k].toFixed(0)}`).join(', ')} = ${total(t).toFixed(0)} ms`).join('; ')
      + `; rectify of the best run: detect ${best.detect.toFixed(0)}, warp ${best.warp.toFixed(0)}, sharpness ${best.sharpness.toFixed(0)} ms`);
    expect(total(best)).toBeLessThan(BUDGET_MS);
  }, 300_000);
});
