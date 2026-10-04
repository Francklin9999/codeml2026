// CSV writers and calliper maths. No personal field in any column (strat18 §4.1): the user agent is allowed, a name is not.
import type { Mode } from './naming';

export const CALLIPER_SPREAD_LIMIT_MM = 0.2;

/** Columns of data/own_lenses.template.csv (brief 14). */
export const OWN_LENSES_COLUMNS = ['lensId', 'description', 'A_mm_1', 'A_mm_2', 'A_mm_3', 'B_mm_1', 'B_mm_2', 'B_mm_3', 'edge_thickness_mm', 'tint', 'notes'] as const;
/** Columns of the eval page results.csv (brief 14). */
export const RESULTS_COLUMNS = ['file', 'lensId', 'phone', 'rep', 'A', 'B', 'perimeter', 'method', 'reprojErrMm', 'sharpness', 'error'] as const;
export const MANIFEST_COLUMNS = [
  'file', 'mode', 'lensId', 'label', 'tags', 'eye', 'phone', 'rep', 'position', 'condition',
  'A_mm_1', 'A_mm_2', 'A_mm_3', 'B_mm_1', 'B_mm_2', 'B_mm_3', 'edge_thickness_mm', 'tint', 'notes',
  'taken_at', 'width', 'height', 'focal35mm', 'bytes', 'user_agent', 'app_version',
  'ok', 'A', 'B', 'perimeter', 'method', 'reprojErrMm', 'sharpness', 'errorCode',
  'sheet_checked', 'sheet_ok', 'sheet_markers', 'exported_at',
] as const;

export function csvEscape(v: unknown): string {
  const s = v === undefined || v === null ? '' : String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** LF line ends, trailing newline. */
export function toCsv(columns: readonly string[], rows: Record<string, unknown>[]): string {
  const lines = [columns.map(csvEscape).join(',')];
  for (const r of rows) lines.push(columns.map((c) => csvEscape(r[c])).join(','));
  return lines.join('\n') + '\n';
}

/** Header of the brief-14 template when it was read, else the default columns. */
export function ownLensesColumns(templateText?: string): string[] {
  const first = templateText?.split(/\r?\n/, 1)[0]?.trim();
  if (first) {
    const cols = first.split(',').map((c) => c.trim());
    if (cols[0] === 'lensId') return cols;
  }
  return [...OWN_LENSES_COLUMNS];
}

export function median(values: number[]): number | null {
  const v = values.filter((x) => Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = v.length >> 1;
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

export function spread(values: number[]): number | null {
  const v = values.filter((x) => Number.isFinite(x));
  return v.length < 2 ? null : Math.max(...v) - Math.min(...v);
}

/** Comma or dot decimal; empty, zero, negative or invalid gives null. */
export function parseDecimal(s: string): number | null {
  const t = s.trim().replace(',', '.');
  if (!/^\d+(\.\d+)?$/.test(t)) return null;
  const n = Number(t);
  return n > 0 ? n : null;
}

export type Readings = (number | null)[];

const present = (r: Readings): number[] => r.filter((x): x is number => x !== null && Number.isFinite(x));

/** Median of the readings that exist (strat2 §5.1: median of three is the reference). */
export function refValue(readings: Readings): number | null {
  return median(present(readings));
}

/** sign = measured minus calliper. null when there is no reading. */
export function signedError(measured: number, readings: Readings): number | null {
  const ref = refValue(readings);
  return ref === null ? null : measured - ref;
}

/** Spread of the readings above 0.2 mm: « lectures incohérentes, refaire ». */
export function inconsistent(readings: Readings): boolean {
  const s = spread(present(readings));
  return s !== null && s > CALLIPER_SPREAD_LIMIT_MM + 1e-9;
}

/** Everything the manifest needs, no image bytes. */
export interface Meta {
  name: string; // file name with extension, unique key
  mode: Mode;
  lensId: string;
  label?: string;
  tags?: string[];
  eye?: 'L' | 'R';
  phone: string;
  rep?: number;
  position?: number;
  condition?: string;
  description?: string;
  A?: Readings;
  B?: Readings;
  edgeThickness?: number | null;
  tint?: string;
  notes?: string;
  takenAt: string;
  width?: number;
  height?: number;
  focal35mm?: number;
  bytes: number;
  mime: string;
  userAgent: string;
  appVersion: string;
  ok: boolean;
  measured?: { A: number; B: number; perimeter: number; method: string; reprojErrMm: number; sharpness: number };
  errorCode?: string;
  sheet?: { checked: boolean; ok: boolean; markers?: number };
  exportedAt?: string;
}

const r = (n: number | undefined | null, d = 3) => (n === undefined || n === null ? '' : Number(n.toFixed(d)));

export function manifestRow(m: Meta): Record<string, unknown> {
  const A = m.A ?? [], B = m.B ?? [];
  return {
    file: m.name, mode: m.mode, lensId: m.lensId, label: m.label, tags: (m.tags ?? []).join(';'), eye: m.eye, phone: m.phone,
    rep: m.rep, position: m.position, condition: m.condition,
    A_mm_1: A[0], A_mm_2: A[1], A_mm_3: A[2], B_mm_1: B[0], B_mm_2: B[1], B_mm_3: B[2],
    edge_thickness_mm: m.edgeThickness, tint: m.tint, notes: m.notes,
    taken_at: m.takenAt, width: m.width, height: m.height, focal35mm: m.focal35mm, bytes: m.bytes,
    user_agent: m.userAgent, app_version: m.appVersion,
    ok: m.ok ? 1 : 0, A: r(m.measured?.A), B: r(m.measured?.B), perimeter: r(m.measured?.perimeter), method: m.measured?.method,
    reprojErrMm: r(m.measured?.reprojErrMm, 4), sharpness: r(m.measured?.sharpness, 6), errorCode: m.errorCode,
    sheet_checked: m.sheet ? (m.sheet.checked ? 1 : 0) : '', sheet_ok: m.sheet?.checked ? (m.sheet.ok ? 1 : 0) : '', sheet_markers: m.sheet?.markers,
    exported_at: m.exportedAt,
  };
}

export function resultsRow(m: Meta): Record<string, unknown> {
  return {
    file: m.name, lensId: m.lensId, phone: m.phone, rep: m.rep,
    A: r(m.measured?.A), B: r(m.measured?.B), perimeter: r(m.measured?.perimeter), method: m.measured?.method,
    reprojErrMm: r(m.measured?.reprojErrMm, 4), sharpness: r(m.measured?.sharpness, 6), error: m.errorCode,
  };
}

/** One row per lens with a validation photo; the latest record that carries readings wins. */
export function ownLensesRows(metas: Meta[]): Record<string, unknown>[] {
  const has = (x: Meta) => [...(x.A ?? []), ...(x.B ?? [])].some((v) => v !== null && v !== undefined);
  const byLens = new Map<string, Meta>();
  for (const m of metas.filter((x) => x.mode === 'validation').sort((a, b) => a.takenAt.localeCompare(b.takenAt))) {
    const prev = byLens.get(m.lensId);
    if (!prev || has(m) || !has(prev)) byLens.set(m.lensId, m);
  }
  return [...byLens.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([lensId, m]) => ({
    lensId, description: m.description, A_mm_1: m.A?.[0], A_mm_2: m.A?.[1], A_mm_3: m.A?.[2],
    B_mm_1: m.B?.[0], B_mm_2: m.B?.[1], B_mm_3: m.B?.[2], edge_thickness_mm: m.edgeThickness, tint: m.tint, notes: m.notes,
  }));
}
