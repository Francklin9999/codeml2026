// The collect page measures with the same steps as the app (worker.ts): rectify -> segmentClassic -> measureLens.
// brief 10's pipeline.measureOne did not exist when this was written; switch the body of `measure` to it when it does.
// Vision code is imported lazily so the page itself stays small and OpenCV loads only at the first shot.
import { OptiError, type BoardSpec, type Eye, type LensMeasurement, type Photo } from '../contracts';
import spec from '../../public/board_spec.json';
import bias from '../../public/bias.json';

export const boardSpec = spec as unknown as BoardSpec;

function wrap(e: unknown): OptiError {
  return e instanceof OptiError ? e : new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e));
}

/** Throws OptiError only. */
export async function measure(photo: Photo, eye: Eye): Promise<LensMeasurement> {
  try {
    const [{ rectify }, { segmentClassic }, { measureLens, setBias }] = await Promise.all([
      import('../vision/rectify'), import('../vision/segmentClassic'), import('../measure'),
    ]);
    setBias(bias); // bias.json is bundled: no fetch
    const r = await rectify(photo, boardSpec);
    return measureLens(r, segmentClassic(r), eye);
  } catch (e) {
    throw wrap(e);
  }
}

/** Sheet check only (training and free modes). Throws OptiError only; resolves with the marker count when it can be read. */
export async function checkSheet(photo: Photo): Promise<{ nMarkers?: number }> {
  try {
    const { rectify, locateReference } = await import('../vision/rectify');
    await rectify(photo, boardSpec);
    // rectify returns no marker count; locateReference is what it calls first.
    let nMarkers: number | undefined;
    try { nMarkers = (await locateReference(photo, boardSpec)).nMarkers; } catch { /* count is optional */ }
    return { nMarkers };
  } catch (e) {
    throw wrap(e);
  }
}
