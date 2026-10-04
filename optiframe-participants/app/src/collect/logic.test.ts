import { describe, expect, it } from 'vitest';
import {
  CONDITIONS, conditionGrid, extensionFor, finalId, freeName, guessPhone, isValidId, nextFreeIndex, nextRep, sanitizeId, trainingName, validationName,
} from './naming';
import {
  MANIFEST_COLUMNS, OWN_LENSES_COLUMNS, RESULTS_COLUMNS, csvEscape, inconsistent, manifestRow, median, ownLensesColumns, ownLensesRows, parseDecimal,
  refValue, resultsRow, signedError, spread, toCsv, type Meta,
} from './manifest';
import { CSV_COLUMNS } from '../eval/parse';

/** independent CSV parser (RFC 4180) used to round-trip */
function parseCsv(s: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], cell = '', q = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === '"' && s[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  return rows;
}

describe('file names', () => {
  it('builds the three patterns', () => {
    expect(validationName('L01', 'Pixel-7', 2)).toBe('L01_Pixel-7_2.jpg');
    expect(trainingName('L07', 3, 'lampL')).toBe('L07_3_lampL.jpg');
    expect(freeName('SN-SF-paire3', 1)).toBe('SN-SF-paire3_1.jpg');
    expect(validationName('L01', 'iPhone', 1, extensionFor('image/heic'))).toBe('L01_iPhone_1.heic');
  });
  it('sanitises identifiers: no underscore, space or accent survives', () => {
    expect(sanitizeId('L 01_a')).toBe('L-01-a');
    expect(sanitizeId('Éléphant/x:y\\z')).toBe('Elephantxyz');
    expect(sanitizeId('a---b')).toBe('a-b');
    expect(sanitizeId('x'.repeat(50))).toHaveLength(32);
    expect(finalId('-L01-')).toBe('L01');
    expect(isValidId('L01')).toBe(true);
    expect(isValidId('L_01')).toBe(false);
    expect(isValidId('')).toBe(false);
    expect(isValidId('a b')).toBe(false);
    expect(isValidId('-a')).toBe(false);
  });
  it('no character forbidden on Windows can come out of sanitising', () => {
    for (const bad of '<>:"/\\|?*_ \t') expect(finalId(`a${bad}b`)).toMatch(/^[A-Za-z0-9-]+$/);
  });
  it('rep counts up per lensId and phone, from 1', () => {
    const rec = (lensId: string, phone: string, rep: number) => ({ mode: 'validation' as const, lensId, phone, rep });
    expect(nextRep([], 'L01', 'p')).toBe(1);
    const ex = [rec('L01', 'p', 1), rec('L01', 'p', 2), rec('L01', 'q', 1), rec('L02', 'p', 1)];
    expect(nextRep(ex, 'L01', 'p')).toBe(3);
    expect(nextRep(ex, 'L01', 'q')).toBe(2);
    expect(nextRep(ex, 'L03', 'p')).toBe(1);
    expect(nextRep(ex, 'l01', 'P')).toBe(3); // case-insensitive: names must stay unique on Windows
    expect(nextRep([rec('L01', 'p', 1), rec('L01', 'p', 3)], 'L01', 'p')).toBe(4); // deleted rep 2 is not reused
    expect(nextRep([{ mode: 'training' as const, lensId: 'L01', phone: 'p', rep: 9 }], 'L01', 'p')).toBe(1);
  });
  it('free index counts per label', () => {
    expect(nextFreeIndex([{ mode: 'free', label: 'a', rep: 1 }, { mode: 'free', label: 'a', rep: 2 }, { mode: 'free', label: 'b', rep: 1 }], 'a')).toBe(3);
    expect(nextFreeIndex([], 'a')).toBe(1);
  });
  it('guesses the phone from the user agent', () => {
    expect(guessPhone('Mozilla/5.0 (Linux; Android 14; Pixel 7 Build/UP1A) Chrome/120')).toBe('Pixel-7');
    expect(guessPhone('Mozilla/5.0 (Linux; Android 10; K) Chrome/120')).toBe('K');
    expect(guessPhone('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari')).toBe('iPhone');
    expect(guessPhone('Mozilla/5.0 (X11; Linux x86_64)')).toBe('phone');
  });
});

describe('condition grid', () => {
  it('keeps easy first, in the protocol order', () => {
    expect(CONDITIONS[0]).toBe('easy');
    expect(CONDITIONS).toEqual(['easy', 'room', 'lampL', 'lampT', 'lampR', 'flash', 'pattern', 'colour']);
    expect(conditionGrid(new Set()).map((g) => g.cond)).toEqual([...CONDITIONS]);
  });
  it('marks done conditions and flags those that would come before easy', () => {
    const none = conditionGrid(new Set());
    expect(none[0]).toMatchObject({ cond: 'easy', late: false });
    expect(none.slice(1).every((g) => g.late)).toBe(true);
    const some = conditionGrid(new Set(['easy', 'room']));
    expect(some.find((g) => g.cond === 'room')).toMatchObject({ done: true, late: false });
    expect(some.find((g) => g.cond === 'flash')).toMatchObject({ done: false, late: false });
    expect(conditionGrid(new Set(['room'])).find((g) => g.cond === 'flash')!.late).toBe(true);
  });
});

describe('calliper maths', () => {
  it('median of three, sign = measured minus calliper', () => {
    expect(median([60.1, 59.9, 60.4])).toBeCloseTo(60.1);
    expect(median([1, 2, 3, 4])).toBe(2.5);
    expect(median([])).toBeNull();
    expect(refValue([60.1, null, 59.9])).toBeCloseTo(60);
    expect(signedError(60.5, [60, 60.1, 59.9])).toBeCloseTo(0.5);
    expect(signedError(59.5, [60, 60.1, 59.9])).toBeCloseTo(-0.5);
    expect(signedError(60, [null, null, null])).toBeNull();
  });
  it('flags a spread above 0.2 mm', () => {
    expect(spread([60, 60.15, 60.1])).toBeCloseTo(0.15);
    expect(inconsistent([60, 60.15, 60.1])).toBe(false);
    expect(inconsistent([60, 60.2, 60.1])).toBe(false);
    expect(inconsistent([60, 60.3, 60.1])).toBe(true);
    expect(inconsistent([60, null, null])).toBe(false);
  });
  it('reads comma and dot decimals, refuses nonsense', () => {
    expect(parseDecimal('60,25')).toBe(60.25);
    expect(parseDecimal(' 60.25 ')).toBe(60.25);
    for (const bad of ['', 'abc', '-3', '0', '1,2,3']) expect(parseDecimal(bad)).toBeNull();
  });
});

const meta = (o: Partial<Meta> = {}): Meta => ({
  name: 'L01_p_1.jpg', mode: 'validation', lensId: 'L01', phone: 'p', rep: 1, eye: 'R', A: [60, 60.1, 59.9], B: [48, 48.1, 48], edgeThickness: 2.1,
  tint: 'clair', notes: 'x', takenAt: '2026-01-01T10:00:00.000Z', bytes: 3, mime: 'image/jpeg', userAgent: 'UA', appVersion: '0.1.0', ok: true,
  measured: { A: 60.12345, B: 48.2, perimeter: 190, method: 'classic', reprojErrMm: 0.1, sharpness: 0.0012 }, ...o,
});

describe('CSV', () => {
  it('escapes commas, quotes and newlines and round-trips', () => {
    const note = 'a, "b"\nc';
    expect(csvEscape(note)).toBe('"a, ""b""\nc"');
    const csv = toCsv(['x', 'y'], [{ x: note, y: 1 }, { x: undefined, y: 'plain' }]);
    expect(parseCsv(csv)).toEqual([['x', 'y'], [note, '1'], ['', 'plain']]);
  });
  it('own_lenses.csv uses the brief-14 columns and results.csv the eval columns', () => {
    expect([...OWN_LENSES_COLUMNS].join(',')).toBe('lensId,description,A_mm_1,A_mm_2,A_mm_3,B_mm_1,B_mm_2,B_mm_3,edge_thickness_mm,tint,notes');
    expect([...RESULTS_COLUMNS].join(',')).toBe('file,lensId,phone,rep,A,B,perimeter,method,reprojErrMm,sharpness,error');
    const csv = toCsv(OWN_LENSES_COLUMNS, ownLensesRows([meta({ notes: 'a,b' })]));
    const [head, row] = parseCsv(csv);
    expect(head).toEqual([...OWN_LENSES_COLUMNS]);
    expect(row).toEqual(['L01', '', '60', '60.1', '59.9', '48', '48.1', '48', '2.1', 'clair', 'a,b']);
  });
  it('results.csv columns equal the eval page CSV_COLUMNS and carry the error code', () => {
    expect([...RESULTS_COLUMNS]).toEqual([...CSV_COLUMNS]);
    expect(resultsRow(meta({ ok: false, measured: undefined, errorCode: 'NO_LENS' })).error).toBe('NO_LENS');
  });
  it('takes the header of the template when given', () => {
    expect(ownLensesColumns('lensId,description,foo\nrow')).toEqual(['lensId', 'description', 'foo']);
    expect(ownLensesColumns('garbage')).toEqual([...OWN_LENSES_COLUMNS]);
    expect(ownLensesColumns(undefined)).toEqual([...OWN_LENSES_COLUMNS]);
  });
  it('one own_lenses row per lens, latest readings win', () => {
    const rows = ownLensesRows([
      meta({ name: 'a', takenAt: '2026-01-01T10:00:00Z', A: [60, 60, 60] }),
      meta({ name: 'b', takenAt: '2026-01-01T11:00:00Z', A: [61, 61, 61] }),
      meta({ name: 'c', takenAt: '2026-01-01T12:00:00Z', A: [null, null, null], B: [null, null, null] }),
      meta({ name: 'd', lensId: 'L02', mode: 'free' }),
    ]);
    expect(rows).toHaveLength(1);
    expect(rows[0].A_mm_1).toBe(61);
  });
  it('manifest has every column, no name field, failure keeps its code', () => {
    expect(MANIFEST_COLUMNS.some((c) => /name$/i.test(c) && c !== 'file')).toBe(false);
    const row = manifestRow(meta({ ok: false, measured: undefined, errorCode: 'NO_LENS' }));
    expect(Object.keys(row).every((k) => (MANIFEST_COLUMNS as readonly string[]).includes(k))).toBe(true);
    expect(row.ok).toBe(0);
    expect(row.errorCode).toBe('NO_LENS');
    expect(resultsRow(meta()).A).toBe(60.123);
  });
});
