import { describe, expect, it } from 'vitest';
import { OptiError, type LensMeasurement } from '../contracts';
import { evaluateFile, parseCsv, parseFileName, parseOwnLenses, toCsv, type ResultRow } from './parse';

const meas = (): LensMeasurement => ({
  eye: 'R', contourMm: [], A: 50.123, B: 40.5, perimeter: 150.2, boxCentre: [0, 0], method: 'classic',
  quality: { reprojErrMm: 0.12, sharpness: 0.0004, nShots: 1, spreadA: 0, spreadB: 0 },
});

describe('parseFileName', () => {
  it('parses lensId_phone_rep.ext', () => {
    expect(parseFileName('L07_pixel7_2.jpg')).toEqual({ lensId: 'L07', phone: 'pixel7', rep: 2 });
    expect(parseFileName('C:\\photos\\L07_iph13_10.JPEG')).toEqual({ lensId: 'L07', phone: 'iph13', rep: 10 });
  });
  it('keeps underscores inside the lensId', () => {
    expect(parseFileName('own_lens_03_phoneA_1.png')).toEqual({ lensId: 'own_lens_03', phone: 'phoneA', rep: 1 });
  });
  it('rejects names that do not follow the convention', () => {
    expect(parseFileName('IMG_0001.jpg')).toBeNull();
    expect(parseFileName('L07_phone_x.jpg')).toBeNull();
    expect(parseFileName('photo.jpg')).toBeNull();
  });
});

describe('toCsv', () => {
  const row = (o: Partial<ResultRow>): ResultRow => ({
    file: 'a.jpg', lensId: 'L1', phone: 'p', rep: 1, A: 50.1, B: 40.2, perimeter: 150, method: 'classic',
    reprojErrMm: 0.1, sharpness: 0.0004, error: '', ...o,
  });
  it('writes the header, empty cells for nulls and quotes special characters', () => {
    const csv = toCsv([row({}), row({ file: 'we,ird "x".jpg', A: null, B: null, perimeter: null, method: '', reprojErrMm: null, sharpness: null, error: 'NO_LENS' })]);
    expect(csv.split('\n')).toEqual([
      'file,lensId,phone,rep,A,B,perimeter,method,reprojErrMm,sharpness,error',
      'a.jpg,L1,p,1,50.1,40.2,150,classic,0.1,0.0004,',
      '"we,ird ""x"".jpg",L1,p,1,,,,,,,NO_LENS',
      '',
    ]);
  });
  it('round-trips through the CSV reader', () => {
    const rows = parseCsv(toCsv([row({ file: 'a,"b".jpg' })]));
    expect(rows[1][0]).toBe('a,"b".jpg');
    expect(rows[0]).toHaveLength(11);
  });
});

describe('evaluateFile', () => {
  it('fills the row from the measurement', async () => {
    const r = await evaluateFile('L07_p1_3.jpg', async () => meas());
    expect(r).toMatchObject({ lensId: 'L07', phone: 'p1', rep: 3, A: 50.123, B: 40.5, perimeter: 150.2, method: 'classic', reprojErrMm: 0.12, sharpness: 0.0004, error: '' });
  });
  it('turns OptiError and other failures into an error code, never a throw', async () => {
    expect((await evaluateFile('L07_p1_3.jpg', async () => { throw new OptiError('NO_LENS'); })).error).toBe('NO_LENS');
    const r = await evaluateFile('L07_p1_3.jpg', async () => { throw new Error('boom'); });
    expect(r.error).toBe('LOAD_FAILED');
    expect(r.A).toBeNull();
  });
  it('flags a bad file name without measuring', async () => {
    let called = false;
    const r = await evaluateFile('IMG_1.jpg', async () => { called = true; return meas(); });
    expect(r.error).toBe('BAD_FILE_NAME');
    expect(called).toBe(false);
  });
});

describe('parseOwnLenses', () => {
  it('takes the median of the readings and skips EXAMPLE rows', () => {
    const csv = 'lensId,description,A_mm_1,A_mm_2,A_mm_3,B_mm_1,B_mm_2,B_mm_3,edge_thickness_mm,tint,notes\r\n'
      + 'EXAMPLE_L01,"x, y",50,50,50,40,40,40,,,\r\n'
      + 'L01,"round, clear",50.0,50.4,50.1,40.2,40.0,,,,\r\n';
    const m = parseOwnLenses(csv);
    expect([...m.keys()]).toEqual(['L01']);
    expect(m.get('L01')!.A).toBeCloseTo(50.1);
    expect(m.get('L01')!.B).toBeCloseTo(40.1);
  });
});
