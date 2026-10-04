import { OptiError, type Pt } from '../contracts';
import { boxing } from './boxing';

/** The lens edge sits this far above the sheet, so it looks larger than the sheet under it. */
export const EDGE_HEIGHT_MM = 3;
const MIN_PLAUSIBLE_DIST_MM = 100; // a phone cannot focus closer; a smaller D is a bad estimate, not a correction

/** Scale about the window centre by (D - h) / D. Unknown or implausible D: no scaling. */
export function parallaxCorrect(c: Pt[], cameraDistMm: number | undefined, windowMm: { w: number; h: number }): Pt[] {
  const D = cameraDistMm;
  if (D === undefined || !Number.isFinite(D) || D < MIN_PLAUSIBLE_DIST_MM) return c;
  const f = (D - EDGE_HEIGHT_MM) / D;
  const cx = windowMm.w / 2, cy = windowMm.h / 2;
  return c.map(([x, y]) => [cx + (x - cx) * f, cy + (y - cy) * f] as Pt);
}

export interface Bias { a0: number; a1: number; b0: number; b1: number }
const IDENTITY: Bias = { a0: 0, a1: 1, b0: 0, b1: 1 };
let bias: Bias = { ...IDENTITY };

function check(b: Bias): Bias {
  const ok = [b.a0, b.a1, b.b0, b.b1].every(Number.isFinite) && b.a1 > 0 && b.b1 > 0;
  if (!ok) throw new OptiError('LOAD_FAILED', 'bias needs finite a0, a1, b0, b1 with a1 > 0 and b1 > 0');
  return { a0: b.a0, a1: b.a1, b0: b.b0, b1: b.b1 };
}

/** Extra keys (fittedOn, nLenses, ...) are ignored. No argument: back to identity. */
export function setBias(b?: Bias): void {
  bias = b === undefined ? { ...IDENTITY } : check(b);
}

export function getBias(): Bias {
  return { ...bias };
}

export async function loadBias(url: string): Promise<void> {
  let j: Record<string, unknown>;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(String(res.status));
    const body: unknown = await res.json();
    if (body === null || typeof body !== 'object') throw new Error('not an object');
    j = body as Record<string, unknown>;
  } catch (e) {
    throw new OptiError('LOAD_FAILED', 'bias.json: ' + (e instanceof Error ? e.message : String(e)));
  }
  setBias({ a0: Number(j.a0), a1: Number(j.a1), b0: Number(j.b0), b1: Number(j.b1) });
}

/** A' = a0 + a1 A and B' = b0 + b1 B, applied to the contour itself (scaled about the box centre). */
export function biasCorrect(c: Pt[]): Pt[] {
  const m = boxing(c);
  const A = bias.a0 + bias.a1 * m.A, B = bias.b0 + bias.b1 * m.B;
  if (!(A > 0 && B > 0)) throw new OptiError('NO_LENS', 'bias gives a non-positive size');
  const sx = A / m.A, sy = B / m.B;
  if (sx === 1 && sy === 1) return c;
  const [cx, cy] = m.boxCentre;
  return c.map(([x, y]) => [cx + (x - cx) * sx, cy + (y - cy) * sy] as Pt);
}
