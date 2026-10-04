import { describe, expect, it } from 'vitest';
import { DEFAULT_FRAME, OptiError, type Eye, type FrameParams, type FrameResult, type LensMeasurement, type Pt } from '../contracts';
import { generateFrame, loadManifold } from './index';
import { layoutLenses } from './layout';
import { bbox, cleanContour, signedArea } from './polygons';

// ---- synthetic inputs -------------------------------------------------------------------------
function ellipse(w: number, h: number, cx = 30, cy = 20, n = 180): Pt[] {
  return Array.from({ length: n }, (_, i) => {
    const t = (2 * Math.PI * i) / n;
    return [cx + (w / 2) * Math.cos(t), cy - (h / 2) * Math.sin(t)] as Pt;
  });
}

function roundedRect(w: number, h: number, r: number, cx = 30, cy = 20, perCorner = 24): Pt[] {
  const pts: Pt[] = [];
  const corners: [number, number, number][] = [[w / 2 - r, h / 2 - r, 0], [-(w / 2 - r), h / 2 - r, 90], [-(w / 2 - r), -(h / 2 - r), 180], [w / 2 - r, -(h / 2 - r), 270]];
  for (const [ox, oy, a0] of corners) {
    for (let k = 0; k <= perCorner; k++) {
      const a = ((a0 + (90 * k) / perCorner) * Math.PI) / 180;
      pts.push([cx + ox + r * Math.cos(a), cy - (oy + r * Math.sin(a))]);
    }
  }
  return pts;
}

function lens(eye: Eye, contourMm: Pt[]): LensMeasurement {
  const b = bbox(contourMm);
  return {
    eye, contourMm, A: b.maxX - b.minX, B: b.maxY - b.minY, perimeter: 0,
    boxCentre: [(b.minX + b.maxX) / 2, (b.minY + b.maxY) / 2], method: 'classic',
    quality: { reprojErrMm: 0, sharpness: 0, nShots: 1, spreadA: 0, spreadB: 0 },
  };
}

const params = (o: Partial<FrameParams> = {}): FrameParams => ({ ...DEFAULT_FRAME, ...o });

// ---- mesh checks (strat9 T1, T2) --------------------------------------------------------------
interface MeshReport { watertight: boolean; badEdges: number; zeroArea: number; volume: number; bodies: number }

function checkMesh(f: FrameResult): MeshReport {
  const { positions: P, indices: I } = f;
  // Weld vertices by position so a duplicated vertex cannot hide an open edge.
  const ids = new Map<string, number>();
  const id: number[] = [];
  for (let v = 0; v < P.length / 3; v++) {
    const key = `${Math.round(P[3 * v] * 1e4)},${Math.round(P[3 * v + 1] * 1e4)},${Math.round(P[3 * v + 2] * 1e4)}`;
    if (!ids.has(key)) ids.set(key, ids.size);
    id.push(ids.get(key)!);
  }
  const directed = new Map<string, number>();
  const parent = Array.from({ length: ids.size }, (_, i) => i);
  const find = (a: number): number => (parent[a] === a ? a : (parent[a] = find(parent[a])));
  let zeroArea = 0;
  let volume = 0;
  for (let t = 0; t < I.length; t += 3) {
    const v = [I[t], I[t + 1], I[t + 2]];
    const a = v.map((k) => [P[3 * k], P[3 * k + 1], P[3 * k + 2]]);
    const u = [a[1][0] - a[0][0], a[1][1] - a[0][1], a[1][2] - a[0][2]];
    const w = [a[2][0] - a[0][0], a[2][1] - a[0][1], a[2][2] - a[0][2]];
    const cr = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]];
    if (Math.hypot(cr[0], cr[1], cr[2]) / 2 < 1e-9) zeroArea++;
    volume += (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0]) + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])) / 6;
    for (let e = 0; e < 3; e++) {
      const p = id[v[e]], q = id[v[(e + 1) % 3]];
      const key = `${p}>${q}`;
      directed.set(key, (directed.get(key) ?? 0) + 1);
      parent[find(p)] = find(q);
    }
  }
  let badEdges = 0;
  for (const [key, n] of directed) {
    const [p, q] = key.split('>');
    if (n !== 1 || directed.get(`${q}>${p}`) !== 1 || p === q) badEdges++;
  }
  const bodies = new Set(Array.from(ids.values(), (i) => find(i))).size;
  return { watertight: badEdges === 0, badEdges, zeroArea, volume, bodies };
}

function expectSolid(f: FrameResult): void {
  const r = checkMesh(f);
  expect(r.badEdges).toBe(0);
  expect(r.zeroArea).toBe(0);
  expect(r.volume).toBeGreaterThan(0);
  expect(r.bodies).toBe(1);
}

// ---- geometry helpers ------------------------------------------------------------------------
function distToSegment(p: Pt, a: Pt, b: Pt): number {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const l2 = dx * dx + dy * dy;
  const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2));
  return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
}
function distToPoly(p: Pt, poly: readonly Pt[]): number {
  let d = Infinity;
  for (let i = 0; i < poly.length; i++) d = Math.min(d, distToSegment(p, poly[i], poly[(i + 1) % poly.length]));
  return d;
}
function inside(p: Pt, poly: readonly Pt[]): boolean {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > p[1] !== yj > p[1] && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}
/** Input contour moved the way the layout moves it (frame coordinates, y down). */
function placed(c: Pt[], side: 'right' | 'left', bridge: number): Pt[] {
  const b = bbox(c);
  const dx = side === 'right' ? -bridge / 2 - b.maxX : bridge / 2 - b.minX;
  return c.map(([x, y]) => [x + dx, y - (b.minY + b.maxY) / 2] as Pt);
}
const maxX = (p: Pt[]) => Math.max(...p.map((q) => q[0]));
const minX = (p: Pt[]) => Math.min(...p.map((q) => q[0]));

// ---- tests ------------------------------------------------------------------------------------
describe('layout (pure)', () => {
  it('puts the nasal edges bridgeMm apart, right lens on -x, box centres on y = 0', () => {
    const lay = layoutLenses(ellipse(50, 36, 80, 55), roundedRect(52, 34, 8, 10, 10), params({ bridgeMm: 17 }));
    expect(maxX(lay.right)).toBeCloseTo(-8.5, 9);
    expect(minX(lay.left)).toBeCloseTo(8.5, 9);
    const rb = bbox(lay.right), lb = bbox(lay.left);
    expect((rb.minY + rb.maxY) / 2).toBeCloseTo(0, 9);
    expect((lb.minY + lb.maxY) / 2).toBeCloseTo(0, 9);
  });

  it('places the bridge bar 4 mm high, centred 3 mm above y = 0 (y down: -3)', () => {
    const lay = layoutLenses(ellipse(50, 36), ellipse(50, 36), params());
    const b = bbox(lay.bridge);
    expect(b.maxY - b.minY).toBeCloseTo(4, 9);
    expect((b.minY + b.maxY) / 2).toBeCloseTo(-3, 9);
  });

  it('puts a tenon overlapping the rim by 1 mm on each temporal extreme', () => {
    const p = params();
    const lay = layoutLenses(ellipse(50, 36), ellipse(50, 36), p);
    const reach = p.clearanceMm + p.rimWidthMm;
    const [tr, tl] = lay.tenons;
    expect(bbox(tr.rect).maxX).toBeCloseTo(minX(lay.right) - reach + 1, 9);
    expect(bbox(tl.rect).minX).toBeCloseTo(maxX(lay.left) + reach - 1, 9);
    expect(bbox(tr.rect).maxX - bbox(tr.rect).minX).toBeCloseTo(p.tenonMm.w, 9);
    expect(bbox(tr.rect).maxY - bbox(tr.rect).minY).toBeCloseTo(p.tenonMm.h, 9);
  });

  it('cleanContour drops points closer than 0.05 mm and rejects degenerate input', () => {
    const c = cleanContour([[0, 0], [0.01, 0], [10, 0], [10, 0.02], [10, 10], [0, 10]]);
    expect(c).toHaveLength(4);
    expect(signedArea(c)).toBeCloseTo(100, 9);
    expect(() => cleanContour([[0, 0], [1, 1]])).toThrow(OptiError);
    expect(() => cleanContour([[0, 0], [NaN, 1], [3, 3]])).toThrow(OptiError);
  });
});

describe('generateFrame', () => {
  const cases: [string, Pt[], Pt[]][] = [
    ['two ellipses 50x36', ellipse(50, 36), ellipse(50, 36, 90, 12)],
    ['ellipse + rounded rectangle 52x34', ellipse(50, 36), roundedRect(52, 34, 8, 70, 15)],
  ];

  it.each(cases)('is watertight, consistent, one body, positive volume: %s', async (_n, rc, lc) => {
    const f = await generateFrame(lens('L', lc), lens('R', rc), params());
    expectSolid(f);
    expect(f.gapMm).toBeGreaterThan(0.19); // measured on the generated seats, not copied from the parameter
    expect(f.gapMm).toBeLessThan(0.21);
    expect(f.positions.length / 3).toBeGreaterThan(100);
    // z up from the bed
    let zMin = Infinity, zMax = -Infinity;
    for (let i = 2; i < f.positions.length; i += 3) { zMin = Math.min(zMin, f.positions[i]); zMax = Math.max(zMax, f.positions[i]); }
    expect(zMin).toBeCloseTo(0, 5);
    expect(zMax).toBeCloseTo(4, 5);
  });

  it('the mesh check really detects an open or flipped mesh', async () => {
    const f = await generateFrame(lens('L', ellipse(50, 36)), lens('R', ellipse(50, 36)), params());
    expect(checkMesh({ ...f, indices: f.indices.slice(3) }).badEdges).toBeGreaterThan(0);
    const flipped = f.indices.slice();
    [flipped[1], flipped[2]] = [flipped[2], flipped[1]];
    expect(checkMesh({ ...f, indices: flipped }).badEdges).toBeGreaterThan(0);
  });

  it('is watertight over the sweep clearance 0.1-0.3, bridge 14-22, rim 2.5-5', async () => {
    const rc = ellipse(50, 36), lc = roundedRect(52, 34, 8);
    for (const clearanceMm of [0.1, 0.2, 0.3]) {
      for (const bridgeMm of [14, 18, 22]) {
        for (const rimWidthMm of [2.5, 3.5, 5]) {
          const f = await generateFrame(lens('L', lc), lens('R', rc), params({ clearanceMm, bridgeMm, rimWidthMm }));
          expectSolid(f);
        }
      }
    }
  }, 60_000);

  it('seat outline is at clearance +-0.02 mm from the input contour, for both lens shapes', async () => {
    const rc = ellipse(50, 36), lc = roundedRect(52, 34, 8, 70, 15);
    for (const clearanceMm of [0.1, 0.2, 0.3]) {
      const p = params({ clearanceMm });
      const f = await generateFrame(lens('L', lc), lens('R', rc), p);
      for (const [seat, input] of [[f.seatR, placed(rc, 'right', p.bridgeMm)], [f.seatL, placed(lc, 'left', p.bridgeMm)]] as const) {
        expect(seat.length).toBeGreaterThan(50);
        for (let i = 0; i < seat.length; i++) {
          const a = seat[i], b = seat[(i + 1) % seat.length];
          for (const q of [a, [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2] as Pt]) {
            expect(Math.abs(distToPoly(q, input) - clearanceMm)).toBeLessThanOrEqual(0.02);
            expect(inside(q, input)).toBe(false);
          }
        }
        // same winding sign as the input contour
        expect(Math.sign(signedArea(seat))).toBe(Math.sign(signedArea(rc)));
      }
    }
  });

  it('keeps the nasal edges bridgeMm apart (seat edges are clearance outside them)', async () => {
    for (const bridgeMm of [14, 18, 22]) {
      const p = params({ bridgeMm });
      const f = await generateFrame(lens('L', roundedRect(52, 34, 8)), lens('R', ellipse(50, 36)), p);
      const nasalGap = minX(f.seatL) - maxX(f.seatR) + 2 * p.clearanceMm;
      expect(Math.abs(nasalGap - bridgeMm)).toBeLessThanOrEqual(0.01);
      // right lens on -x
      expect(maxX(f.seatR)).toBeLessThan(0);
      expect(minX(f.seatL)).toBeGreaterThan(0);
    }
  });

  it('generates in under 2 s, including the first WASM load', async () => {
    const t0 = performance.now();
    await generateFrame(lens('L', roundedRect(52, 34, 8)), lens('R', ellipse(50, 36)), params());
    console.info(`frame generation, cold: ${Math.round(performance.now() - t0)} ms`);
    expect(performance.now() - t0).toBeLessThan(2000);
    const t1 = performance.now();
    await generateFrame(lens('L', ellipse(50, 36, 30, 20, 600)), lens('R', ellipse(50, 36, 30, 20, 600)), params());
    console.info(`frame generation, warm, 600-point contours: ${Math.round(performance.now() - t1)} ms`);
    expect(performance.now() - t1).toBeLessThan(2000);
  });

  it('survives duplicate points, a clockwise contour and a tiny self-intersection', async () => {
    const base = ellipse(50, 36);
    const dirty: Pt[] = [];
    base.forEach((p, i) => {
      dirty.push(p, [p[0] + 0.001, p[1]]);
      if (i === 20) dirty.push([p[0] + 0.3, p[1] + 0.5], [p[0] - 0.2, p[1] + 0.4]); // small loop crossing the outline
    });
    const f = await generateFrame(lens('L', dirty.reverse()), lens('R', base), params());
    expectSolid(f);
  });

  it('throws OptiError (never another exception) on unusable input', async () => {
    const good = lens('R', ellipse(50, 36));
    await expect(generateFrame(lens('L', [[0, 0], [1, 1]]), good, params())).rejects.toBeInstanceOf(OptiError);
    await expect(generateFrame(lens('L', ellipse(50, 36)), good, params({ thicknessMm: -1 }))).rejects.toBeInstanceOf(OptiError);
    await expect(generateFrame(lens('L', ellipse(1, 1)), good, params())).rejects.toBeInstanceOf(OptiError); // lens smaller than the lip
    await expect(generateFrame(lens('L', ellipse(50, 36)), good, params({ tenonMm: { w: 6, h: 8, hole: 5 } }))).rejects.toBeInstanceOf(OptiError);
  });
});

// Printability (strat9 4.2): flat on the bed, no supports. Check the layers by slicing the final mesh.
describe('printability', () => {
  it('layer openings follow the lip rule, no opening is smaller than the lip allows, hinge holes go through', async () => {
    const m = await loadManifold();
    const p = params();
    const rc = ellipse(50, 36), lc = roundedRect(52, 34, 8, 70, 15);
    const f = await generateFrame(lens('L', lc), lens('R', rc), p);
    const mesh = new m.Mesh({ numProp: 3, vertProperties: f.positions, triVerts: f.indices });
    const solid = m.Manifold.ofMesh(mesh);
    try {
      const T = p.thicknessMm;
      const holesAt = (z: number): Pt[][] => {
        const cs = solid.slice(z);
        try {
          return (cs.toPolygons() as Pt[][]).filter((poly) => signedArea(poly) < 0);
        } finally { cs.delete(); }
      };
      const flip = (poly: Pt[]) => poly.map(([x, y]) => [x, -y] as Pt); // slice is y up, inputs are y down
      const inputs = [placed(rc, 'right', p.bridgeMm), placed(lc, 'left', p.bridgeMm)];
      const openingFor = (hs: Pt[][], input: Pt[]) => {
        const h = hs.find((poly) => inside(flip(poly)[0], input) || distToPoly(flip(poly)[0], input) < 1.5);
        return h ? flip(h) : undefined;
      };
      const seats: Pt[][] = [];
      for (const z of [0.125 * T, 0.5 * T, 0.875 * T]) {
        const hs = holesAt(z);
        expect(hs.length).toBeGreaterThanOrEqual(2); // two lens openings (the hinge holes do not cut these planes' outline)
        const lensHoles = inputs.map((inp) => openingFor(hs, inp));
        lensHoles.forEach((h, k) => {
          expect(h, `opening of lens ${k} at z=${z}`).toBeDefined();
          const isLip = z !== 0.5 * T;
          const want = isLip ? p.lipMm : p.clearanceMm;
          for (const q of h!) {
            expect(Math.abs(distToPoly(q, inputs[k]) - want)).toBeLessThanOrEqual(0.02);
            expect(inside(q, inputs[k])).toBe(isLip); // lip opening lies inside the lens outline, seat outside
          }
          if (!isLip) seats[k] = h!;
        });
      }
      // Overhang of a lip over the groove wall = lip + clearance. Never more.
      for (const z of [0.125 * T, 0.875 * T]) {
        openingFor(holesAt(z), inputs[0])!.forEach((q) => {
          expect(distToPoly(q, seats[0])).toBeLessThanOrEqual(p.lipMm + p.clearanceMm + 0.02);
        });
      }
      // Through holes: at mid-thickness a slot is open at the hinge axis, at the bed the solid is closed there.
      const slotAt = (z: number, pt: Pt): boolean => {
        const cs = solid.slice(z);
        try { return (cs.toPolygons() as Pt[][]).filter((poly) => inside(pt, poly)).length % 2 === 0; } finally { cs.delete(); }
      };
      const lay = layoutLenses(rc, lc, p);
      for (const t of lay.tenons) {
        const c: Pt = [t.holeX, -(t.yMin + t.yMax) / 2];
        expect(slotAt(T / 2, c)).toBe(true);
        expect(slotAt(0.05, c)).toBe(false);
      }
    } finally {
      solid.delete();
    }
  });
});
