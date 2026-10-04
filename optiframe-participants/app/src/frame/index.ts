import Module, { type CrossSection as CrossSectionT, type Manifold as ManifoldT, type ManifoldToplevel } from 'manifold-3d';
import { OptiError, type FrameParams, type FrameResult, type LensMeasurement, type Pt } from '../contracts';
import { layoutLenses } from './layout';
import { cleanContour, signedArea } from './polygons';

// Layers along z (print bed at z = 0): back lip, groove, front lip. Fractions of thicknessMm.
const LIP_FRACTION = 0.25;
// Round joins: segments per 360 degrees. Keeps arcs within about 5 microns, even at the 0.2 mm seat radius.
const JOIN_SEGMENTS = 64;
const HOLE_SEGMENTS = 24;
const SIMPLIFY_MM = 0.005;

let wasm: Promise<ManifoldToplevel> | undefined;

function wasmUrl(): string | undefined {
  if (typeof location === 'undefined') return undefined; // Node (tests): the package finds its own .wasm
  // Page: next to index.html. Worker: the bundle sits in assets/, so one level up.
  const base = typeof document !== 'undefined' ? document.baseURI : new URL('../', location.href).href;
  return new URL('vendor/manifold/manifold.wasm', base).href;
}

/** The WASM module, loaded once. The .wasm is self-hosted in public/vendor/manifold/. */
export function loadManifold(): Promise<ManifoldToplevel> {
  wasm ??= (async () => {
    const url = wasmUrl();
    const m = await Module(url ? { locateFile: () => url } : undefined);
    m.setup();
    return m;
  })();
  wasm.catch(() => { wasm = undefined; }); // let a later call retry
  return wasm;
}

function checkParams(p: FrameParams): void {
  const t = p.tenonMm;
  const ok = [p.bridgeMm, p.rimWidthMm, p.thicknessMm, p.lipMm, t?.w, t?.h, t?.hole].every((v) => Number.isFinite(v) && v > 0)
    && Number.isFinite(p.clearanceMm) && p.clearanceMm >= 0
    && t.hole < p.thicknessMm && t.w > 1 && p.rimWidthMm > 0;
  if (!ok) throw new OptiError('LOAD_FAILED', 'invalid frame parameters');
}

type Owned = { delete(): void };

async function build(left: LensMeasurement, right: LensMeasurement, p: FrameParams): Promise<FrameResult> {
  checkParams(p);
  const m = await loadManifold();
  const { CrossSection, Manifold } = m;
  const owned: Owned[] = [];
  const own = <T extends Owned>(x: T): T => { owned.push(x); return x; };
  const up = (pts: readonly Pt[]): Pt[] => pts.map(([x, y]) => [x, -y] as Pt); // frame is y down, the model y up
  const down = up;

  // The model is built y up so the mesh is a proper right-handed solid seen from the front.
  const largest = (cs: CrossSectionT): Pt[] | undefined => {
    let best: Pt[] | undefined;
    let bestA = 0;
    for (const poly of cs.toPolygons()) {
      const a = signedArea(poly as Pt[]);
      if (a > bestA) { best = poly as Pt[]; bestA = a; }
    }
    return best;
  };

  // Drop near-duplicate points, then a union removes self-intersections; keep the biggest outline (no holes).
  const simple = (lens: LensMeasurement): Pt[] => {
    const cs = own(CrossSection.ofPolygons([up(cleanContour(lens.contourMm))], 'NonZero'));
    const s = own(cs.simplify(SIMPLIFY_MM));
    const poly = largest(s);
    if (!poly) throw new OptiError('NO_LENS', 'contour is empty after cleaning');
    return down(poly);
  };

  try {
    const rightPts = simple(right);
    const leftPts = simple(left);
    const lay = layoutLenses(rightPts, leftPts, p);
    const contours = [lay.right, lay.left];

    const seats: CrossSectionT[] = [];
    const lipOpenings: CrossSectionT[] = [];
    const outers: CrossSectionT[] = [];
    for (const c of contours) {
      const cs = own(CrossSection.ofPolygons([up(c)], 'NonZero'));
      seats.push(own(cs.offset(p.clearanceMm, 'Round', 2, JOIN_SEGMENTS)));
      const lip = own(cs.offset(-p.lipMm, 'Round', 2, JOIN_SEGMENTS));
      if (lip.isEmpty()) throw new OptiError('NO_LENS', 'lens too small for the lip');
      lipOpenings.push(lip);
      outers.push(own(cs.offset(p.clearanceMm + p.rimWidthMm, 'Round', 2, JOIN_SEGMENTS)));
    }

    const solid = own(CrossSection.union([
      ...outers,
      own(CrossSection.ofPolygons([up(lay.bridge)], 'NonZero')),
      ...lay.tenons.map((t) => own(CrossSection.ofPolygons([up(t.rect)], 'NonZero'))),
    ]));
    const lipLayer = own(CrossSection.difference([solid, own(CrossSection.union(lipOpenings))]));
    const grooveLayer = own(CrossSection.difference([solid, own(CrossSection.union(seats))]));

    const T = p.thicknessMm;
    const lipH = T * LIP_FRACTION;
    const slab = (cs: CrossSectionT, z0: number, h: number): ManifoldT => own(own(cs.extrude(h)).translate(0, 0, z0));
    let body: ManifoldT = own(Manifold.union([
      slab(lipLayer, 0, lipH),
      slab(grooveLayer, lipH, T - 2 * lipH),
      slab(lipLayer, T - lipH, lipH),
    ]));

    // Hinge pin holes: cylinders along y, a little longer than the tenon block.
    const holes = lay.tenons.map((t) => {
      const len = t.yMax - t.yMin + 1;
      const cyl = own(Manifold.cylinder(len, p.tenonMm.hole / 2, p.tenonMm.hole / 2, HOLE_SEGMENTS, true));
      const turned = own(cyl.rotate(90, 0, 0)); // z axis -> y axis
      return own(turned.translate(t.holeX, -(t.yMin + t.yMax) / 2, T / 2));
    });
    body = own(Manifold.difference([body, ...holes]));

    if (body.status() !== 'NoError' || body.isEmpty() || body.volume() <= 0) throw new OptiError('LOAD_FAILED', 'frame solid is invalid');
    const parts = body.decompose();
    parts.forEach(own);
    if (parts.length !== 1) throw new OptiError('NO_LENS', 'frame is not one connected piece');

    const mesh = body.getMesh();
    const nv = mesh.vertProperties.length / mesh.numProp;
    const positions = new Float32Array(nv * 3);
    for (let i = 0; i < nv; i++) {
      positions[3 * i] = mesh.vertProperties[i * mesh.numProp];
      positions[3 * i + 1] = mesh.vertProperties[i * mesh.numProp + 1];
      positions[3 * i + 2] = mesh.vertProperties[i * mesh.numProp + 2];
    }
    const indices = Uint32Array.from(mesh.triVerts);

    // Seat outlines in frame coordinates, same winding as the input contour.
    const seatOutline = (cs: CrossSectionT, input: readonly Pt[]): Pt[] => {
      const poly = largest(cs);
      if (!poly) throw new OptiError('NO_LENS', 'seat is empty');
      const pts = down(poly);
      return Math.sign(signedArea(pts)) === Math.sign(signedArea(input)) ? pts : pts.reverse();
    };
    const seatR = seatOutline(seats[0], right.contourMm);
    const seatL = seatOutline(seats[1], left.contourMm);
    // Gap actually produced by the offset: half the growth of the boxing extents, averaged over both axes and both lenses.
    const growth = (seat: Pt[], input: readonly Pt[]) => {
      const [sw, sh] = extents(seat), [cw, ch] = extents(input);
      return (sw - cw + sh - ch) / 4;
    };
    return {
      positions,
      indices,
      seatR,
      seatL,
      gapMm: (growth(seatR, right.contourMm) + growth(seatL, left.contourMm)) / 2,
    };
  } finally {
    for (let i = owned.length - 1; i >= 0; i--) {
      try { owned[i].delete(); } catch { /* already freed */ }
    }
  }
}

function extents(p: readonly Pt[]): [number, number] {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of p) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  return [x1 - x0, y1 - y0];
}

/** Frame front for the wearer's `left` and `right` lenses. Never throws anything but OptiError. */
export async function generateFrame(left: LensMeasurement, right: LensMeasurement, p: FrameParams): Promise<FrameResult> {
  try {
    return await build(left, right, p);
  } catch (e) {
    if (e instanceof OptiError) throw e;
    throw new OptiError('LOAD_FAILED', e instanceof Error ? e.message : String(e));
  }
}
