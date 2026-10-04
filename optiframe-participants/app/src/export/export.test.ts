// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest';
import { DEFAULT_FRAME, OptiError, type FrameResult, type LensMeasurement, type Pt } from '../contracts';
import { contourToSvg, meshToStl, measurementToJson, saveBlob, FILE_NAMES } from './index';

function ellipse(a: number, b: number, cx = 30, cy = 20, n = 90): Pt[] {
  return Array.from({ length: n }, (_, i) => { const t = (2 * Math.PI * i) / n; return [cx + (a / 2) * Math.cos(t), cy - (b / 2) * Math.sin(t)] as Pt; });
}
function lens(eye: 'L' | 'R', A: number, B: number): LensMeasurement {
  const c = ellipse(A, B);
  const xs = c.map(p => p[0]), ys = c.map(p => p[1]);
  const aa = Math.max(...xs) - Math.min(...xs), bb = Math.max(...ys) - Math.min(...ys);
  return { eye, contourMm: c, A: aa, B: bb, perimeter: 150, boxCentre: [30, 20], method: 'classic',
    quality: { reprojErrMm: 0.05, sharpness: 120, nShots: 3, spreadA: 0.1, spreadB: 0.1 } };
}

describe('contourToSvg', () => {
  for (const [A, B] of [[50, 36], [75, 75], [40, 30]]) {
    it(`parses back, A=${A} B=${B}`, () => {
      const m = lens('R', A, B);
      const doc = new DOMParser().parseFromString(contourToSvg(m), 'image/svg+xml');
      expect(doc.querySelector('parsererror')).toBeNull();
      const root = doc.documentElement;
      const [, , vw, vh] = root.getAttribute('viewBox')!.split(' ').map(Number);
      expect(root.getAttribute('width')).toBe(`${vw.toFixed(2)}mm`);
      expect(root.getAttribute('height')).toBe(`${vh.toFixed(2)}mm`);
      expect(vw).toBeLessThanOrEqual(190);
      expect(vh).toBeLessThanOrEqual(250);
      const paths = [...doc.querySelectorAll('path')];
      const contour = paths.find(p => p.getAttribute('id') !== 'scale-bar')!;
      expect(contour.getAttribute('fill')).toBe('none');
      expect(contour.getAttribute('stroke-width')).toBe('0.2');
      const d = contour.getAttribute('d')!;
      expect((d.match(/M/g) ?? []).length).toBe(1);
      expect(d.trim().endsWith('Z')).toBe(true);
      const pts = [...d.matchAll(/[ML]\s*(-?[\d.]+)\s+(-?[\d.]+)/g)].map(r => [+r[1], +r[2]]);
      const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
      expect(Math.abs(Math.max(...xs) - Math.min(...xs) - m.A)).toBeLessThan(0.01);
      expect(Math.abs(Math.max(...ys) - Math.min(...ys) - m.B)).toBeLessThan(0.01);
      expect(Math.min(...ys)).toBeGreaterThanOrEqual(10 - 0.01);
      const bar = paths.find(p => p.getAttribute('id') === 'scale-bar')!.getAttribute('d')!;
      const first = bar.match(/M([\d.]+) ([\d.]+) L([\d.]+) ([\d.]+)/)!;
      expect(+first[3] - +first[1]).toBe(50);
      expect(+first[4]).toBe(+first[2]);
      const texts = [...doc.querySelectorAll('text')].map(t => t.textContent);
      expect(texts).toContain('50 mm');
      expect(texts).toContain('Imprimer à 100 % (taille réelle)');
      expect(texts).toContain(`A = ${m.A.toFixed(1)} mm  B = ${m.B.toFixed(1)} mm`);
      expect(texts).toContain('Œil droit');
      const rect = doc.querySelector('rect')!;
      expect(rect.getAttribute('stroke-dasharray')).toBeTruthy();
      expect(parseFloat(rect.getAttribute('width')!)).toBeCloseTo(m.A, 1);
    });
  }
  it('left eye label', () => {
    expect(contourToSvg(lens('L', 50, 36))).toContain('Œil gauche');
  });
});

describe('meshToStl', () => {
  const f: FrameResult = {
    positions: new Float32Array([0, 0, 0, 3, 0, 0, 0, 4, 0, 0, 0, 5, 1.5, 2.25, -1]),
    indices: new Uint32Array([0, 1, 2, 0, 2, 3, 1, 4, 3]), seatL: [], seatR: [], gapMm: 18,
  };
  it('round-trips', () => {
    const buf = meshToStl(f);
    expect(buf.byteLength).toBe(84 + 50 * 3);
    const dv = new DataView(buf);
    expect(dv.getUint32(80, true)).toBe(3);
    for (let t = 0; t < 3; t++) {
      const o = 84 + 50 * t;
      const nrm = [0, 1, 2].map(k => dv.getFloat32(o + 4 * k, true));
      expect(Math.hypot(...nrm)).toBeCloseTo(1, 5);
      for (let v = 0; v < 3; v++) for (let k = 0; k < 3; k++)
        expect(dv.getFloat32(o + 12 + 12 * v + 4 * k, true)).toBe(f.positions[f.indices[3 * t + v] * 3 + k]);
      expect(dv.getUint16(o + 48, true)).toBe(0);
    }
    expect(dv.getFloat32(84 + 8, true)).toBe(1); // first triangle normal +z
  });
});

describe('measurementToJson', () => {
  it('round-trips', () => {
    const l = lens('L', 50, 36), r = lens('R', 52, 34);
    const s = measurementToJson(l, r, DEFAULT_FRAME, '0.1.0', '2026-10-03');
    const o = JSON.parse(s);
    expect(o.left).toEqual(JSON.parse(JSON.stringify(l)));
    expect(o.right).toEqual(JSON.parse(JSON.stringify(r)));
    expect(o.frameParams).toEqual(DEFAULT_FRAME);
    expect(o.appVersion).toBe('0.1.0');
    expect(o.date).toBe('2026-10-03');
    expect(measurementToJson(l, r, DEFAULT_FRAME, '0.1.0', '2026-10-03')).toBe(s);
  });
});

describe('invalid input throws OptiError', () => {
  it('svg: empty contour, NaN point, non-finite A', () => {
    expect(() => contourToSvg({ ...lens('R', 50, 36), contourMm: [] })).toThrow(OptiError);
    expect(() => contourToSvg({ ...lens('R', 50, 36), contourMm: [[0, 0], [NaN, 1], [2, 2]] })).toThrow(OptiError);
    expect(() => contourToSvg({ ...lens('R', 50, 36), A: Infinity })).toThrow(OptiError);
  });
  it('json: non-finite A, B, quality, params', () => {
    const l = lens('L', 50, 36), r = lens('R', 52, 34);
    expect(() => measurementToJson({ ...l, A: NaN, B: Infinity }, r, DEFAULT_FRAME, '0.1.0', 'd')).toThrow(OptiError);
    expect(() => measurementToJson(l, { ...r, quality: { ...r.quality, sharpness: NaN } }, DEFAULT_FRAME, '0.1.0', 'd')).toThrow(OptiError);
    expect(() => measurementToJson(l, r, { ...DEFAULT_FRAME, bridgeMm: Infinity }, '0.1.0', 'd')).toThrow(OptiError);
    expect(() => measurementToJson({ ...l, contourMm: [[0, NaN]] }, r, DEFAULT_FRAME, '0.1.0', 'd')).toThrow(OptiError);
  });
  it('stl: NaN position, index out of range', () => {
    const ok = { positions: new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]), indices: new Uint32Array([0, 1, 2]), seatL: [], seatR: [], gapMm: 18 };
    expect(() => meshToStl({ ...ok, positions: new Float32Array([0, 0, 0, NaN, 0, 0, 0, 1, 0]) })).toThrow(OptiError);
    expect(() => meshToStl({ ...ok, indices: new Uint32Array([0, 1, 3]) })).toThrow(OptiError);
    expect(() => meshToStl(ok)).not.toThrow();
  });
});

describe('saveBlob', () => {
  it('clicks a temporary link and revokes later', () => {
    vi.useFakeTimers();
    const create = vi.fn(() => 'blob:x'), revoke = vi.fn();
    URL.createObjectURL = create;
    URL.revokeObjectURL = revoke;
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    saveBlob('a', FILE_NAMES.json, 'application/json');
    expect(click).toHaveBeenCalled();
    expect(revoke).not.toHaveBeenCalled();
    vi.advanceTimersByTime(5000);
    expect(revoke).toHaveBeenCalledWith('blob:x');
    expect(document.querySelector('a[download]')).toBeNull();
    vi.useRealTimers();
  });
  it('file names', () => {
    expect(Object.values(FILE_NAMES)).toEqual(['contour-gauche.svg', 'contour-droit.svg', 'monture.stl', 'mesures.json']);
  });
});
