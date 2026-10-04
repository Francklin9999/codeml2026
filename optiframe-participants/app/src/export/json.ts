import { OptiError, type FrameParams, type LensMeasurement } from '../contracts';

const lens = (m: LensMeasurement) => ({
  eye: m.eye, A: m.A, B: m.B, perimeter: m.perimeter, boxCentre: m.boxCentre,
  method: m.method, quality: m.quality, contourMm: m.contourMm,
});

/** Stable document: fixed key order, app version and date come from the caller. */
export function measurementToJson(left: LensMeasurement, right: LensMeasurement, params: FrameParams, appVersion: string, date: string): string {
  // JSON.stringify would turn NaN and Infinity into null: refuse instead.
  const refuse = (_k: string, v: unknown) => {
    if (typeof v === 'number' && !Number.isFinite(v)) throw new OptiError('NO_LENS', 'export: non-finite number in measurement');
    return v;
  };
  return JSON.stringify({ app: 'OptiFrame', appVersion, date, units: 'mm', left: lens(left), right: lens(right), frameParams: params }, refuse, 2);
}
