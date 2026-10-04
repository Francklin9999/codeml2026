// Segmentation benchmark through the app's own code: segmentClassic, then the model fallback exactly as
// worker.ts chains them (classic first, model when classic says NO_LENS or scores below LOW_MASK_SCORE),
// then measureLens. Input: a folder written by training/data/make_bench.py (800x650 PNG windows + truth.csv).
// Not part of `npm test`: run it on purpose with
//   BENCH_DIR=<folder> BENCH_MODEL=<lens_seg.onnx> npx vitest run --config bench/vitest.bench.config.ts
// Writes <folder>/bench_results.csv (or BENCH_OUT) and a _summary.json beside it.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { PNG } from 'pngjs';
import { expect, it, vi } from 'vitest';
import { OptiError, type Mask, type Rectified } from '../src/contracts';
import { measureLens } from '../src/measure';
import { segmentClassic } from '../src/vision/segmentClassic';
import { getLastTimings, isModelAvailable, segmentModel, setAssetBase } from '../src/vision/segmentModel';
import { LOW_MASK_SCORE } from '../src/worker';

const dir = process.env.BENCH_DIR ?? '';
const modelPath = process.env.BENCH_MODEL ?? '';
const limit = Number(process.env.BENCH_LIMIT ?? '0');
const outName = process.env.BENCH_OUT ?? 'bench_results.csv';

interface Row { file: string; scene: string; A: number; B: number }
interface Outcome { code: string; A?: number; B?: number; score?: number }

function readTruth(): Row[] {
  const lines = readFileSync(resolve(dir, 'truth.csv'), 'utf8').trim().split(/\r?\n/);
  const head = lines[0].split(',');
  const col = (n: string) => head.indexOf(n);
  return lines.slice(1).map((l) => {
    const c = l.split(',');
    return { file: c[col('file')], scene: c[col('scene')], A: Number(c[col('A_mm')]), B: Number(c[col('B_mm')]) };
  });
}

function loadRectified(file: string): Rectified {
  const png = PNG.sync.read(readFileSync(resolve(dir, file)));
  const image = new ImageData(new Uint8ClampedArray(png.data.buffer, png.data.byteOffset, png.data.length), png.width, png.height);
  return { image, pxPerMm: 10, H: [10, 0, 0, 0, 10, 0, 0, 0, 1], reprojErrMm: 0, sharpness: 1 };
}

function measure(r: Rectified, m: Mask): Outcome {
  try {
    const res = measureLens(r, m, 'R');
    return { code: 'OK', A: res.A, B: res.B, score: m.score };
  } catch (e) {
    return { code: e instanceof OptiError ? e.code : 'CRASH' };
  }
}

const errCode = (e: unknown) => (e instanceof OptiError ? e.code : 'CRASH');

it.skipIf(!dir || !existsSync(resolve(dir, 'truth.csv')))('segmentation benchmark', async () => {
  let haveModel = false;
  if (modelPath) {
    const bytes = readFileSync(modelPath);
    vi.stubGlobal('fetch', async () => new Response(bytes, { status: 200, headers: { 'content-type': 'application/octet-stream' } }));
    setAssetBase(pathToFileURL(resolve(import.meta.dirname, '../public') + '/').href);
    haveModel = await isModelAvailable();
    expect(haveModel).toBe(true);
  }
  let rows = readTruth();
  if (limit > 0) rows = rows.slice(0, limit);
  const out: string[] = ['file,scene,A_true,B_true,classic_code,classic_score,classic_A,classic_B,model_code,model_score,model_A,model_B,model_ms,pipe_method,pipe_code,pipe_A,pipe_B'];
  const runMs: number[] = [];
  for (const row of rows) {
    const r = loadRectified(row.file);
    let classic: Outcome = { code: 'NONE' };
    let classicMask: Mask | undefined;
    try {
      classicMask = segmentClassic(r);
      classic = measure(r, classicMask);
    } catch (e) {
      classic = { code: errCode(e) };
    }
    let model: Outcome = { code: 'NONE' };
    let modelMask: Mask | undefined;
    let ms = NaN;
    if (haveModel) {
      try {
        modelMask = await segmentModel(r);
        ms = getLastTimings().runMs;
        runMs.push(ms);
        model = measure(r, modelMask);
      } catch (e) {
        model = { code: errCode(e) };
      }
    }
    // worker.ts segment(): classic if it scores >= LOW_MASK_SCORE, else the model, else classic, else the classic error
    let pipe: Outcome & { method: string };
    if (classicMask && classicMask.score >= LOW_MASK_SCORE) pipe = { ...classic, method: 'classic' };
    else if (modelMask) pipe = { ...model, method: 'model' };
    else if (classicMask) pipe = { ...classic, method: 'classic' };
    else if (haveModel && model.code !== 'LOAD_FAILED' && model.code !== 'NONE') pipe = { ...model, method: 'model' };
    else pipe = { ...classic, method: 'classic' };
    const f = (v?: number) => (v === undefined ? '' : v.toFixed(3));
    out.push([row.file, row.scene, f(row.A), f(row.B), classic.code, f(classic.score), f(classic.A), f(classic.B),
      model.code, f(model.score), f(model.A), f(model.B), Number.isNaN(ms) ? '' : ms.toFixed(1), pipe.method, pipe.code, f(pipe.A), f(pipe.B)].join(','));
  }
  writeFileSync(resolve(dir, outName), out.join('\n') + '\n');
  writeFileSync(resolve(dir, outName.replace(/\.csv$/, '_summary.json')), JSON.stringify({
    n: rows.length, model: modelPath || null,
    medianModelRunMs: runMs.length ? runMs.sort((a, b) => a - b)[Math.floor(runMs.length / 2)] : null,
  }, null, 2));
}, 3_600_000);
