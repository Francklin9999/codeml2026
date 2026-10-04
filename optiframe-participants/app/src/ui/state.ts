import { DEFAULT_FRAME, type ErrorCode, type Eye, type FrameResult, type LensMeasurement, type Photo } from '../contracts';
import type { Timings } from '../timing';
import type { DebugSteps, EngineState } from '../worker';

export type Screen = 'home' | 'capture' | 'result' | 'frame' | 'steps';

export const SHOTS_PER_LENS = 3;
export const BRIDGE_MIN_MM = 14;
export const BRIDGE_MAX_MM = 22;

export interface State {
  screen: Screen;
  eye: Eye | null;
  /** Shots of the lens being measured. */
  shots: LensMeasurement[];
  /** Fused measurement waiting for "Valider". */
  fused: LensMeasurement | null;
  /** Validated lenses (the only measurements that survive a reload). */
  lenses: Partial<Record<Eye, LensMeasurement>>;
  bridgeMm: number;
  frame: FrameResult | null;
  error: ErrorCode | null;
  hint: ErrorCode | null;
  /** Name of the current step while the app works. */
  busy: string | null;
  /** Images of the last photo, in memory only. timings: duration of each stage of that photo, ms. */
  last: { photo: Photo; steps: DebugSteps; result: LensMeasurement; timings?: Timings } | null;
  /** Durations of the stages that run on the page (fuse, frame, stl), ms: last run of each. */
  timings: Timings;
  /** OpenCV.js in the worker: 'loading' shows a line on the capture screen. */
  engine: EngineState;
}

export function initialState(): State {
  return { screen: 'home', eye: null, shots: [], fused: null, lenses: {}, bridgeMm: DEFAULT_FRAME.bridgeMm, frame: null, error: null, hint: null, busy: null, last: null, timings: {}, engine: 'idle' };
}

const KEY = 'optiframe.v1';

const isPt = (p: unknown): boolean => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite);
const isNum = Number.isFinite;

function validLens(m: any, eye: Eye): m is LensMeasurement {
  return !!m && m.eye === eye && isNum(m.A) && isNum(m.B) && isNum(m.perimeter) && isPt(m.boxCentre)
    && (m.method === 'classic' || m.method === 'model')
    && Array.isArray(m.contourMm) && m.contourMm.length >= 3 && m.contourMm.every(isPt)
    && !!m.quality && ['reprojErrMm', 'sharpness', 'nShots', 'spreadA', 'spreadB'].every((k) => isNum(m.quality[k]));
}

/** Measurements only, never images. Storage may be missing or blocked: every call is guarded. */
export function saveState(s: State, storage: Storage | null): void {
  try {
    storage?.setItem(KEY, JSON.stringify({ lenses: s.lenses, bridgeMm: s.bridgeMm }));
  } catch { /* private mode or quota: the app works without it */ }
}

export function restoreState(s: State, storage: Storage | null): void {
  try {
    const raw = storage?.getItem(KEY);
    if (!raw) return;
    const j = JSON.parse(raw);
    for (const eye of ['L', 'R'] as Eye[]) if (validLens(j?.lenses?.[eye], eye)) s.lenses[eye] = j.lenses[eye];
    if (isNum(j?.bridgeMm)) s.bridgeMm = Math.min(BRIDGE_MAX_MM, Math.max(BRIDGE_MIN_MM, j.bridgeMm));
  } catch { /* corrupt entry: start empty */ }
}
