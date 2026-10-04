import { OptiError, type FrameResult } from '../contracts';
import { requireFinite } from './check';

/** Binary STL, little-endian, mm. Normals are computed from the vertices. */
export function meshToStl(f: FrameResult): ArrayBuffer {
  requireFinite(f.positions, 'mesh position');
  const nVerts = Math.floor(f.positions.length / 3);
  for (let i = 0; i < f.indices.length; i++) {
    if (f.indices[i] >= nVerts) throw new OptiError('NO_LENS', 'export: mesh index out of range');
  }
  const tris = Math.floor(f.indices.length / 3);
  const buf = new ArrayBuffer(84 + 50 * tris);
  const dv = new DataView(buf);
  const head = new TextEncoder().encode('OptiFrame binary STL, units mm');
  new Uint8Array(buf, 0, 80).set(head.subarray(0, 80));
  dv.setUint32(80, tris, true);
  const p = f.positions;
  let o = 84;
  for (let t = 0; t < tris; t++) {
    const a = f.indices[3 * t] * 3, b = f.indices[3 * t + 1] * 3, c = f.indices[3 * t + 2] * 3;
    const ux = p[b] - p[a], uy = p[b + 1] - p[a + 1], uz = p[b + 2] - p[a + 2];
    const vx = p[c] - p[a], vy = p[c + 1] - p[a + 1], vz = p[c + 2] - p[a + 2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz) || 1; // degenerate triangle: zero normal
    nx /= len; ny /= len; nz /= len;
    for (const v of [nx, ny, nz]) { dv.setFloat32(o, v, true); o += 4; }
    for (const i of [a, b, c]) for (let k = 0; k < 3; k++) { dv.setFloat32(o, p[i + k], true); o += 4; }
    dv.setUint16(o, 0, true); o += 2;
  }
  return buf;
}
