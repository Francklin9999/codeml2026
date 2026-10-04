// The collect page measures with pipeline.measureOne (same path as the app). The pipeline is imported lazily; OpenCV loads in its worker at the first shot.
import { OptiError, type BoardSpec, type Eye, type LensMeasurement, type Photo } from '../contracts';
import spec from '../../public/board_spec.json';

export const boardSpec = spec as unknown as BoardSpec;

function wrap(e: unknown): OptiError {
  return e instanceof OptiError ? e : new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e));
}

/** Throws OptiError only. Runs brief 10's pipeline (worker, bias, same path as the app). */
export async function measure(photo: Photo, eye: Eye): Promise<LensMeasurement> {
  try {
    const { measureOne } = await import('../pipeline');
    return await measureOne(photo, eye);
  } catch (e) {
    throw wrap(e);
  }
}

/** Sheet check only (training and free modes). Throws OptiError only; resolves with the marker count when it can be read. */
export async function checkSheet(photo: Photo): Promise<{ nMarkers?: number }> {
  try {
    // In the worker, like a measurement: OpenCV.js is never loaded on the page's own thread.
    const { checkSheet: check } = await import('../pipeline');
    return await check(photo);
  } catch (e) {
    throw wrap(e);
  }
}
