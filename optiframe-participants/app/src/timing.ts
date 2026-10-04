// Stage durations in milliseconds, so the team can read phone timings on the "Pas à pas" screen without a debugger.
// One collector per thread: the worker handles one photo at a time (pipeline.ts queues them).
export type Timings = Record<string, number>;

export const now = (): number => (typeof performance !== 'undefined' ? performance.now() : Date.now());

let current: Timings = {};

export function resetTimings(): void { current = {}; }
/** Adds to the stage (a stage that runs twice for one photo shows its total). */
export function addTiming(stage: string, ms: number): void { current[stage] = (current[stage] ?? 0) + ms; }
export function takeTimings(): Timings { return { ...current }; }

/** Runs f and records its duration, also when it throws. */
export function timed<T>(stage: string, f: () => T): T {
  const t0 = now();
  try { return f(); } finally { addTiming(stage, now() - t0); }
}
export async function timedAsync<T>(stage: string, f: () => Promise<T>): Promise<T> {
  const t0 = now();
  try { return await f(); } finally { addTiming(stage, now() - t0); }
}
