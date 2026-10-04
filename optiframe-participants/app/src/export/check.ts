import { OptiError } from '../contracts';

/** Exports must never write NaN or Infinity: a corrupt jury file is worse than an error. */
export function requireFinite(values: ArrayLike<number>, what: string): void {
  for (let i = 0; i < values.length; i++) {
    if (!Number.isFinite(values[i])) throw new OptiError('NO_LENS', `export: non-finite ${what}`);
  }
}
