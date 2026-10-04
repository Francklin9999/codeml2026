import { OptiError, type Eye, type LensMeasurement, type Mask, type Rectified } from '../contracts';
import { boxing, minAreaRect } from './boxing';
import { biasCorrect, parallaxCorrect } from './correction';
import { contourFromMask } from './contour';

export { setBias, loadBias } from './correction';
export { extentAlong } from './boxing';

const ROTATION_LIMIT_DEG = 5;
const NEAR_CIRCULAR = 1.1;

export function measureLens(r: Rectified, m: Mask, eye: Eye): LensMeasurement {
  try {
    const win = { w: r.image.width / r.pxPerMm, h: r.image.height / r.pxPerMm };
    const contourMm = biasCorrect(parallaxCorrect(contourFromMask(r, m), r.cameraDistMm, win));
    const { A, B, boxCentre, perimeter } = boxing(contourMm);
    return {
      eye, contourMm, A, B, perimeter, boxCentre, method: m.method,
      quality: { reprojErrMm: r.reprojErrMm, sharpness: r.sharpness, nShots: 1, spreadA: 0, spreadB: 0 },
    };
  } catch (e) {
    if (e instanceof OptiError) throw e;
    throw new OptiError('NO_LENS', e instanceof Error ? e.message : String(e));
  }
}

/**
 * Angle in degrees (absolute, 0..90) between the long side of the minimum-area rectangle and the board
 * x axis, when it exceeds 5 degrees and the shape is not near-circular; otherwise null. The UI shows LENS_ROTATED.
 * Near-circular is judged on the rectangle's long/short ratio, which also holds when the lens is turned
 * towards 45 degrees (A/B alone would then read 1).
 */
export function rotationWarningDeg(m: LensMeasurement): number | null {
  const rect = minAreaRect(m.contourMm);
  if (!(rect.short > 0) || rect.long / rect.short <= NEAR_CIRCULAR) return null;
  const dev = Math.abs(rect.longAngleDeg);
  return dev > ROTATION_LIMIT_DEG ? dev : null;
}
