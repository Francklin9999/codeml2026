import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { PNG } from 'pngjs';
import { OptiError, type BoardSpec, type Pt } from '../contracts';
import { applyH } from './homography';
import { loadOpenCv } from './opencv';
import { MAX_EDGE_WIDTH_PX, MIN_SHARPNESS, edgeWidthPx, locateReference, rectify } from './rectify';

// Photos rendered by the reference-sheet rig (brief 02), when they exist: the known homography is the ground truth.
// Every fixture is a usable photo (blur sigma 0.7-1.5 px, the faint-rim ones included): each must be ACCEPTED, and an
// error of any code, BLURRY included, fails the test with that code.
const root = new URL('../../../rig/out/', import.meta.url);
const present = existsSync(new URL('board_spec.json', root)) && existsSync(new URL('fixtures/', root));
const names = present ? readdirSync(new URL('fixtures/', root)).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5)).sort() : [];

describe.skipIf(!present)('rectify on rig fixtures', () => {
  const spec = (): BoardSpec => JSON.parse(readFileSync(new URL('board_spec.json', root), 'utf8'));
  const sharpness: Record<string, number> = {};
  const blur: Record<string, number> = {};

  it('the rig produced the 10 fixtures', () => { expect(names).toHaveLength(10); });

  for (const name of names) {
    it(`${name}: ACCEPTED, H within 1 px of the rig's homography`, async () => {
      const meta = JSON.parse(readFileSync(new URL(`fixtures/${name}.json`, root), 'utf8'));
      const png = PNG.sync.read(readFileSync(new URL(`fixtures/${name}.png`, root)));
      const photo = { image: new ImageData(new Uint8ClampedArray(png.data), png.width, png.height), source: 'file' as const };
      const s = spec();
      const ref = await locateReference(photo, s);
      let worst = 0;
      for (const p of [[0, 0], [80, 0], [80, 65], [0, 65]] as Pt[]) {
        const a = applyH(ref.H, p), b = applyH(meta.H, p);
        worst = Math.max(worst, Math.hypot(a[0] - b[0], a[1] - b[1]));
      }
      let outcome = 'ACCEPTED', r;
      try { r = await rectify(photo, s); } catch (e) { outcome = e instanceof OptiError ? e.message : 'crash: ' + String(e); }
      console.log(`${name}: ${outcome}, worst window-corner offset ${worst.toFixed(3)} px, reproj ${ref.reprojErrMm.toFixed(3)} mm, ${ref.nMarkers} markers, sharpness ${r?.sharpness.toFixed(5)}, blur ${meta.blurSigmaPx} px`);
      expect(outcome).toBe('ACCEPTED');
      expect(worst).toBeLessThan(1);
      expect(r!.image.width).toBe(800);
      expect(r!.image.height).toBe(650);
      expect(r!.sharpness).toBeGreaterThan(MIN_SHARPNESS);
      sharpness[name] = r!.sharpness;
      blur[name] = meta.blurSigmaPx;
    }, 120_000);
  }

  // A photo blurred as a whole loses its markers before the sharpness gate is reached: the error must still say BLURRY.
  const heavy = [{ sigma: 4, noise: 0 }, { sigma: 4, noise: 3 }, { sigma: 6, noise: 0 }, { sigma: 6, noise: 3 }];
  for (const pick of ['fixture_00', 'fixture_04', 'fixture_09']) {
    it(`${pick} blurred as a whole by a further sigma of 4 and 6 px (noise 0 and 3) is BLURRY, whatever the marker detection says`, async () => {
      const name = names.find((n) => n.startsWith(pick))!;
      const png = PNG.sync.read(readFileSync(new URL(`fixtures/${name}.png`, root)));
      const cv = await loadOpenCv();
      const src = new cv.Mat(png.height, png.width, cv.CV_8UC4);
      src.data.set(png.data);
      expect(edgeWidthPx(cv, new ImageData(new Uint8ClampedArray(png.data), png.width, png.height))).toBeLessThan(MAX_EDGE_WIDTH_PX); // the sharp photo is not flagged
      for (const { sigma, noise } of heavy) {
        const b = new cv.Mat();
        cv.GaussianBlur(src, b, new cv.Size(0, 0), sigma, sigma);
        const px = new Uint8ClampedArray(b.data);
        b.delete();
        let seed = 99; // LCG, same noise for every run
        const rand = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
        if (noise) for (let i = 0; i < px.length; i += 4) { const n = Math.sqrt(-2 * Math.log(rand() + 1e-12)) * Math.cos(2 * Math.PI * rand()) * noise; for (let c = 0; c < 3; c++) px[i + c] = Math.round(px[i + c] + n); }
        let outcome = 'ACCEPTED';
        try { await rectify({ image: new ImageData(px, png.width, png.height), source: 'file' }, spec()); } catch (e) { outcome = e instanceof OptiError ? e.code : 'crash: ' + String(e); }
        expect(outcome, `${name} sigma ${sigma} noise ${noise}`).toBe('BLURRY');
      }
      src.delete();
    }, 300_000);
  }

  it('sharpness follows the blur of the photo, not the window content (faint rims are not blurrier than the blurry fixture)', () => {
    const blurriest = names.reduce((a, b) => (blur[b] > blur[a] ? b : a));
    expect(blur[blurriest]).toBe(1.5);
    for (const n of names) if (blur[n] <= 1.0) expect(sharpness[n], n).toBeGreaterThan(sharpness[blurriest]);
  });
});
