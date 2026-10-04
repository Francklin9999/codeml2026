import { OptiError, type ErrorCode, type LensMeasurement } from '../contracts';

export interface PhotoId { lensId: string; phone: string; rep: number }

/** `<lensId>_<phone>_<rep>.jpg`: split from the right, so a lensId may contain underscores. */
export function parseFileName(name: string): PhotoId | null {
  const base = name.replace(/^.*[\\/]/, '').replace(/\.[A-Za-z0-9]+$/, '');
  const m = /^(.+)_([^_]+)_(\d+)$/.exec(base);
  return m ? { lensId: m[1], phone: m[2], rep: Number(m[3]) } : null;
}

export interface ResultRow {
  file: string; lensId: string; phone: string; rep: number | null;
  A: number | null; B: number | null; perimeter: number | null; method: string;
  reprojErrMm: number | null; sharpness: number | null; error: string;
}

export const CSV_COLUMNS = ['file', 'lensId', 'phone', 'rep', 'A', 'B', 'perimeter', 'method', 'reprojErrMm', 'sharpness', 'error'] as const;

const cell = (v: string | number | null): string => {
  if (v === null) return '';
  const s = typeof v === 'number' ? (Number.isFinite(v) ? String(v) : '') : v;
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};

export function toCsv(rows: ResultRow[]): string {
  const lines = [CSV_COLUMNS.join(',')];
  for (const r of rows) lines.push(CSV_COLUMNS.map((c) => cell(r[c])).join(','));
  return lines.join('\n') + '\n';
}

/** One row per photo. Never throws: any failure becomes an error code in the row. */
export async function evaluateFile(file: string, measure: () => Promise<LensMeasurement>): Promise<ResultRow> {
  const id = parseFileName(file);
  const row: ResultRow = {
    file, lensId: id?.lensId ?? '', phone: id?.phone ?? '', rep: id?.rep ?? null,
    A: null, B: null, perimeter: null, method: '', reprojErrMm: null, sharpness: null, error: '',
  };
  if (!id) return { ...row, error: 'BAD_FILE_NAME' };
  try {
    const m = await measure();
    return {
      ...row, A: m.A, B: m.B, perimeter: m.perimeter, method: m.method,
      reprojErrMm: m.quality.reprojErrMm, sharpness: m.quality.sharpness,
    };
  } catch (e) {
    const code: ErrorCode = e instanceof OptiError ? e.code : 'LOAD_FAILED';
    return { ...row, error: code };
  }
}

/** Minimal CSV reader (RFC 4180 quotes), enough for own_lenses.csv. */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let f = '';
  let q = false;
  const endRow = () => {
    row.push(f);
    f = '';
    if (row.some((x) => x !== '')) rows.push(row);
    row = [];
  };
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { f += '"'; i++; }
      else if (c === '"') q = false;
      else f += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      endRow();
    } else f += c;
  }
  endRow();
  return rows;
}

const median = (v: number[]): number => {
  const s = [...v].sort((a, b) => a - b);
  const h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
};

/** lensId -> median of the calliper readings per axis; EXAMPLE rows are skipped like in accuracy_report.py. */
export function parseOwnLenses(text: string): Map<string, { A?: number; B?: number }> {
  const [head, ...body] = parseCsv(text);
  const out = new Map<string, { A?: number; B?: number }>();
  if (!head) return out;
  const idCol = head.indexOf('lensId');
  if (idCol < 0) return out;
  for (const r of body) {
    const lensId = (r[idCol] ?? '').trim();
    if (!lensId || lensId.toUpperCase().startsWith('EXAMPLE')) continue;
    const ref: { A?: number; B?: number } = {};
    for (const ax of ['A', 'B'] as const) {
      const v = [1, 2, 3].map((i) => parseFloat(r[head.indexOf(`${ax}_mm_${i}`)] ?? '')).filter(Number.isFinite);
      if (v.length) ref[ax] = median(v);
    }
    out.set(lensId, ref);
  }
  return out;
}
