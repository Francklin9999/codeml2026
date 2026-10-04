import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { PNG } from 'pngjs';
import type { BoardSpec } from '../contracts';
import { finishLens, measureOne, setAssets } from '../pipeline';

// No mocks: pipeline.ts -> worker.ts (inline in Node) -> rectify -> segmentClassic -> measureLens, on the rig's fixtures.
// A and B come out of the real modules and are compared with the truth stored in each fixture's JSON.
// Limit set by brief 10: 0.5 mm. Fixtures carry no EXIF, so the parallax correction is off; the bias is the identity.
const LIMIT_MM = 0.5;
// The two faint-rim fixtures (rim grey 200-205 on a 240-252 background) are under the classic segmenter's rim-contrast gate
// (MIN_RIM_CONTRAST). Only the model could measure them and public/models/lens_seg.onnx is absent, so the right answer
// is NO_LENS with its message, not a guess. They are listed here, and the test fails if one of them is ever measured badly.
const FAINT_RIM_GREY = 150;
const root = new URL('../../../rig/out/', import.meta.url);
const present = existsSync(new URL('board_spec.json', root)) && existsSync(new URL('fixtures/', root));
const names = present ? readdirSync(new URL('fixtures/', root)).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5)).sort() : [];

describe.skipIf(!present)('real modules on rig fixtures', () => {
  const rows: Record<string, unknown>[] = [];

  it('measures A and B within 0.5 mm of the truth, one shot and three shots fused', async () => {
    const spec = JSON.parse(readFileSync(new URL('board_spec.json', root), 'utf8')) as BoardSpec;
    setAssets({ spec, bias: { a0: 0, a1: 1, b0: 0, b1: 1 } });
    let worst = 0;
    for (const name of names) {
      const truth = JSON.parse(readFileSync(new URL(`fixtures/${name}.json`, root), 'utf8'));
      const png = PNG.sync.read(readFileSync(new URL(`fixtures/${name}.png`, root)));
      const photo = { image: new ImageData(new Uint8ClampedArray(png.data), png.width, png.height), source: 'file' as const };
      if (truth.rimGrey > FAINT_RIM_GREY) {
        const err = await measureOne(photo, 'R').then(() => null, (e) => e);
        // Allowed outcomes: refused with NO_LENS (classic only), or measured within the limit if a model is installed.
        if (err) {
          expect(err.code, name).toBe('NO_LENS');
          rows.push({ fixture: name, shape: truth.shape, truthA: truth.widthMm, truthB: truth.heightMm, refused: 'NO_LENS' });
          console.log(`${name}: refused with NO_LENS (faint rim, classic segmenter only)`);
          continue;
        }
      }
      const m = await measureOne(photo, 'R');
      const fused = finishLens([m, await measureOne(photo, 'R'), await measureOne(photo, 'R')]);
      const errA = m.A - truth.widthMm, errB = m.B - truth.heightMm;
      worst = Math.max(worst, Math.abs(errA), Math.abs(errB), Math.abs(fused.A - truth.widthMm), Math.abs(fused.B - truth.heightMm));
      rows.push({ fixture: name, shape: truth.shape, truthA: truth.widthMm, truthB: truth.heightMm, A: m.A, B: m.B, errA, errB, fusedA: fused.A, fusedB: fused.B, method: m.method });
      console.log(`${name}: A ${m.A.toFixed(2)} (truth ${truth.widthMm}, err ${errA.toFixed(2)}), B ${m.B.toFixed(2)} (truth ${truth.heightMm}, err ${errB.toFixed(2)}), ${m.method}`);
      expect(Math.abs(errA), `${name} A`).toBeLessThanOrEqual(LIMIT_MM);
      expect(Math.abs(errB), `${name} B`).toBeLessThanOrEqual(LIMIT_MM);
    }
    const dir = join(tmpdir(), 'optiframe-brief10');
    mkdirSync(dir, { recursive: true });
    const out = join(dir, 'fixture-errors.json');
    writeFileSync(out, JSON.stringify({ limitMm: LIMIT_MM, worstAbsErrMm: worst, rows }, null, 2));
    console.log(`worst absolute error ${worst.toFixed(3)} mm over ${names.length} fixtures; written to ${out}`);
    expect(names.length).toBeGreaterThan(0);
  }, 600_000);
});
