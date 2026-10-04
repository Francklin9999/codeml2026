// File names and identifiers. Underscore separates the fields of a name, so identifiers never contain one.

export type Mode = 'validation' | 'training' | 'free';
export const MODES: readonly Mode[] = ['validation', 'training', 'free'];
export const MODE_LABEL: Record<Mode, string> = { validation: 'Validation', training: 'Entraînement', free: 'Libre' };

/** Order of the paired-capture grid (strat6 §4.2 / capture_protocol.md): `easy` is shot first. */
export const CONDITIONS = ['easy', 'room', 'lampL', 'lampT', 'lampR', 'flash', 'pattern', 'colour'] as const;
export type Condition = (typeof CONDITIONS)[number];
export const POSITIONS = [1, 2, 3, 4, 5, 6] as const;
export const MAX_ID_LEN = 32;

/** Keeps letters, digits and hyphens. Spaces and underscores become hyphens, accents are dropped, repeated hyphens collapse. */
export function sanitizeId(raw: string): string {
  return raw
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[\s_]+/g, '-')
    .replace(/[^A-Za-z0-9-]/g, '')
    .replace(/-{2,}/g, '-')
    .slice(0, MAX_ID_LEN);
}

/** Same as sanitizeId plus no leading or trailing hyphen: what is used in a file name. */
export function finalId(raw: string): string {
  return sanitizeId(raw).replace(/^-+|-+$/g, '');
}

export function isValidId(s: string): boolean {
  return s.length > 0 && s.length <= MAX_ID_LEN && /^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$/.test(s);
}

export function extensionFor(mime: string): string {
  if (/png/i.test(mime)) return '.png';
  if (/hei[cf]/i.test(mime)) return '.heic';
  return '.jpg';
}

export function validationName(lensId: string, phone: string, rep: number, ext = '.jpg'): string {
  return `${lensId}_${phone}_${rep}${ext}`;
}
export function trainingName(lensId: string, pos: number, cond: Condition, ext = '.jpg'): string {
  return `${lensId}_${pos}_${cond}${ext}`;
}
export function freeName(label: string, n: number, ext = '.jpg'): string {
  return `${label}_${n}${ext}`;
}

interface Numbered { mode: Mode; lensId: string; phone: string; rep?: number }

/** rep counts up per lensId and phone, from 1. Uses max+1, so a deleted photo never frees a name. */
export function nextRep(existing: Numbered[], lensId: string, phone: string): number {
  const l = lensId.toLowerCase(), p = phone.toLowerCase();
  let max = 0;
  for (const r of existing) {
    if (r.mode === 'validation' && r.lensId.toLowerCase() === l && r.phone.toLowerCase() === p) max = Math.max(max, r.rep ?? 0);
  }
  return max + 1;
}

/** n counts up per label, from 1. */
export function nextFreeIndex(existing: { mode: Mode; label?: string; rep?: number }[], label: string): number {
  const l = label.toLowerCase();
  let max = 0;
  for (const r of existing) if (r.mode === 'free' && (r.label ?? '').toLowerCase() === l) max = Math.max(max, r.rep ?? 0);
  return max + 1;
}

/** Android user agents carry the model; iOS ones do not (the user edits the field). */
export function guessPhone(ua: string): string {
  const m = /Android[^;)]*;\s*([^;)]+?)(?:\s+Build|\s*[;)])/.exec(ua);
  if (m) {
    const s = finalId(m[1]);
    if (s) return s;
  }
  if (/iPhone/.test(ua)) return 'iPhone';
  if (/iPad/.test(ua)) return 'iPad';
  if (/Android/.test(ua)) return 'Android';
  return 'phone';
}

export interface ConditionState { cond: Condition; done: boolean; late: boolean }

/** One entry per condition. `late` = shooting it now would come before `easy`. */
export function conditionGrid(done: ReadonlySet<string>): ConditionState[] {
  const easyDone = done.has('easy');
  return CONDITIONS.map((cond) => ({ cond, done: done.has(cond), late: cond !== 'easy' && !easyDone }));
}
