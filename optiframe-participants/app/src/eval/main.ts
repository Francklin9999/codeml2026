/// <reference types="vite/client" />
import { OptiError, type BoardSpec, type Eye, type LensMeasurement, type Photo } from '../contracts';
import { decodeFile } from '../capture';
import { evaluateFile, parseOwnLenses, toCsv, type ResultRow } from './parse';

// Brief 10 owns app/src/pipeline.ts: use its measureOne when the file exists, else the three steps directly.
type MeasureOne = (photo: Photo, eye: Eye) => Promise<LensMeasurement>;
const pipelineModules = import.meta.glob<{ measureOne?: MeasureOne }>('../pipeline.ts');

async function getMeasure(): Promise<{ fn: MeasureOne; source: string }> {
  const load = pipelineModules['../pipeline.ts'];
  const mod = load ? await load() : undefined;
  if (mod?.measureOne) return { fn: mod.measureOne, source: 'src/pipeline.ts measureOne' };
  const [{ rectify }, { segmentClassic }, { measureLens }] = await Promise.all([
    import('../vision/rectify'), import('../vision/segmentClassic'), import('../measure'),
  ]);
  const spec = (await (await fetch(new URL('board_spec.json', document.baseURI))).json()) as BoardSpec;
  return {
    fn: async (photo, eye) => {
      const r = await rectify(photo, spec);
      return measureLens(r, segmentClassic(r), eye);
    },
    source: 'rectify, segmentClassic, measureLens (no src/pipeline.ts)',
  };
}

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const fmt = (v: number | null | undefined, d = 2) => (v === null || v === undefined ? '' : v.toFixed(d));
const HEAD = ['file', 'lensId', 'phone', 'rep', 'A', 'B', 'perimeter', 'method', 'reprojErrMm', 'sharpness', 'error',
  'refA', 'refB', 'errA', 'errB'];
const TEXT_COLS = new Set([0, 1, 2, 7, 10]);
let rows: ResultRow[] = [];

function render(ref: ReturnType<typeof parseOwnLenses>) {
  const table = $<HTMLTableElement>('table');
  table.replaceChildren();
  const hr = table.createTHead().insertRow();
  for (const h of HEAD) hr.appendChild(Object.assign(document.createElement('th'), { textContent: h }));
  const tb = table.createTBody();
  for (const r of rows) {
    const x = ref.get(r.lensId);
    const diff = (m: number | null, k: 'A' | 'B') => (m !== null && x?.[k] !== undefined ? m - x[k]! : null);
    const cells = [r.file, r.lensId, r.phone, r.rep, fmt(r.A), fmt(r.B), fmt(r.perimeter), r.method, fmt(r.reprojErrMm, 3),
      r.sharpness === null ? '' : r.sharpness.toPrecision(3), r.error, fmt(x?.A), fmt(x?.B), fmt(diff(r.A, 'A')), fmt(diff(r.B, 'B'))];
    const tr = tb.insertRow();
    if (r.error) tr.className = 'fail';
    cells.forEach((c, i) => {
      const td = tr.insertCell();
      td.textContent = c === null ? '' : String(c);
      if (!TEXT_COLS.has(i)) td.className = 'num';
    });
  }
}

async function run() {
  const photos = Array.from($<HTMLInputElement>('photos').files ?? []);
  const refFile = $<HTMLInputElement>('ref').files?.[0];
  const ref = refFile ? parseOwnLenses(await refFile.text()) : new Map();
  const eye = $<HTMLSelectElement>('eye').value as Eye;
  const status = $('status');
  $<HTMLButtonElement>('run').disabled = true;
  rows = [];
  try {
    const { fn, source } = await getMeasure();
    for (let i = 0; i < photos.length; i++) {
      status.textContent = `${i + 1} / ${photos.length} (${source})`;
      const file = photos[i];
      rows.push(await evaluateFile(file.name, async () => fn(await decodeFile(file, 'file'), eye)));
      render(ref);
      await new Promise((r) => setTimeout(r)); // let the table paint
    }
    status.textContent = `${photos.length} photos done (${source}); failures: ${rows.filter((r) => r.error).length}`;
  } catch (e) {
    status.textContent = 'Failed: ' + (e instanceof OptiError ? e.code : String(e));
  }
  $<HTMLButtonElement>('run').disabled = false;
  $<HTMLButtonElement>('save').disabled = rows.length === 0;
}

$('run').addEventListener('click', () => void run());
$('save').addEventListener('click', () => {
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([toCsv(rows)], { type: 'text/csv' })), download: 'results.csv',
  });
  a.click();
  URL.revokeObjectURL(a.href);
});
