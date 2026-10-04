export const MAX_SIDE = 4096;
export const MAX_PIXELS = 16_000_000; // under the iOS canvas limit (16 777 216)

/** Size after the downscale rule: longest side <= 4096 px, area <= 16 MP, aspect kept, never upscaled. */
export function fitSize(w: number, h: number): { w: number; h: number } {
  const s = Math.min(1, MAX_SIDE / Math.max(w, h), Math.sqrt(MAX_PIXELS / (w * h)));
  if (s === 1) return { w, h };
  return { w: Math.max(1, Math.floor(w * s)), h: Math.max(1, Math.floor(h * s)) };
}

/** Canvas transform [a,b,c,d,e,f] drawing an unrotated w x h source upright for an EXIF orientation. */
export function orientationMatrix(o: number, w: number, h: number): [number, number, number, number, number, number] {
  switch (o) {
    case 2: return [-1, 0, 0, 1, w, 0];
    case 3: return [-1, 0, 0, -1, w, h];
    case 4: return [1, 0, 0, -1, 0, h];
    case 5: return [0, 1, 1, 0, 0, 0];
    case 6: return [0, 1, -1, 0, h, 0];
    case 7: return [0, -1, -1, 0, h, w];
    case 8: return [0, -1, 1, 0, 0, w];
    default: return [1, 0, 0, 1, 0, 0];
  }
}
