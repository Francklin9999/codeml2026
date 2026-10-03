# OptiFrame · Strategy 9: Parametric frame generator (offset rims, groove, bridge, hinges) → validated STL

| | |
|---|---|
| **Status** | IN PROGRESS — Codex subagent + parent audit, 2026-10-03; Python STL prototype tested, browser/slicer/physical tests NOT RUN |
| **Priority** | P1 (Palier 3 is mandatory) |
| **Effort** | 5–7 h |
| **Depends on** | strategy 8 (canonical contours in mm); can start with two test ellipses 50 × 36 mm |
| **Rubric lines** | Generated frame (10), Contour SVG (5), Mobile app (15: 3D preview + download), Presentation (10) |
| **Work folder** | `optiframe-participants/work/strat9/` (JS module used by the app) |

---

## 1. Context you need

Palier 3: generate a **parametric frame front** from two contours (left and right, possibly different shapes) and the **bridge width (default 18 mm)**; 3D preview in the app; STL download. Rubric: *"STL valide (maillage fermé), cercles cohérents avec les verres (y compris deux formes différentes), pont et tenons présents, imprimable sans supports excessifs."* Tips: keep the contour as a polygon in mm; leave **0.1–0.3 mm clearance** between lens and rim because a real lens is slightly curved. Recommended tools: Clipper (polygon offsetting), three.js (preview, STL export), manifold-3d or JSCAD (3D geometry). Bonus: overlay the measured contour and the generated rim and show the gap in mm.

## 2. The idea

Build the frame front as **2D polygon operations extruded into layers**, so the result is watertight by construction:

1. Rim outer boundary = lens contour offset outward by `rim_width` (e.g. 3–4 mm).
2. Lens seat = lens contour offset outward by `clearance` (0.1–0.3 mm).
3. **Groove** for clipping: a middle layer where the opening is smaller than the lens (lip) or a V-groove approximated by three stacked layers: front lip (opening = contour − 0.5 mm), groove layer (opening = contour + clearance), back lip (opening = contour − 0.5 mm). The lens snaps in by flexing the rim.
4. Bridge = a shaped 2D bar joining the two rims at the nasal sides, length = bridge width (DBL, default 18 mm).
5. Hinge tenons (endpieces) at the temporal sides: blocks with a pin hole sized for standard hinges or a print-in-place pin.
6. Union everything in 2D per layer → extrude → stack → `manifold` union → STL.

## 3. Why it could score

Layered 2D offsetting with Clipper + manifold-3d produces closed, printable meshes reliably and handles two different lens shapes for free. The geometry stays fully parametric (clearance, rim width, bridge width, thickness) for the demo.

## 4. Implementation plan

### 4.1 Files

```
work/strat9/
  frame.js            # contours (mm) + params → manifold → STL (ArrayBuffer)
  params.json         # defaults: rim_width 3.5, thickness 4.0, clearance 0.2, lip 0.5, bridge 18, pantoscopic 0
  svg_export.js       # 1:1 contour + rim outline SVG
  validate_stl.py     # trimesh checks
  test_shapes/        # ellipses, rounded rectangles, two-different-shape pairs
```

### 4.2 Geometry details

```js
// Clipper (clipper2-js or js-angusj-clipper) works in integer units: scale mm by 1000
const seat   = offset(lens, +p.clearance);
const lipOpen= offset(lens, -p.lip);
const outer  = offset(lens, +p.clearance + p.rim_width);
const ringFront  = difference(outer, lipOpen);   // front lip layer
const ringGroove = difference(outer, seat);      // groove layer
const ringBack   = difference(outer, lipOpen);   // back lip layer
// position right rim at x = +(bridge/2 + nasal extent), left rim mirrored
// bridge: polygon connecting the two rims' nasal regions, union with the rings in each layer
// tenons: rectangles at the temporal extremes, extruded thicker, with a cylinder hole (Ø ~1.5 mm) for the hinge screw / pin
```

With manifold-3d (WASM): `CrossSection` from polygons → `.extrude(height)` → `translate` in z → `Manifold.union([...])`. Export: `manifold.getMesh()` → three.js `BufferGeometry` → `STLExporter` (binary).

Printability: lay the front flat (no supports needed); ensure the lip overhang is small (≤ 0.5 mm) or chamfered (use a 45° chamfer layer stack: 3 thin layers with progressively smaller openings).

### 4.3 Two different lenses

Left and right contours come from strategy 8 in canonical orientation (nasal side towards the bridge). The frame's horizontal centre line aligns the two **boxing centres** (or the datum line); the bridge length is measured between the nasal boxing edges (DBL).

### 4.4 Preview and overlay (bonus)

three.js scene with orbit controls; 2D overlay view showing the measured contour, the seat outline and the outer rim, with the computed gap in mm (should equal `clearance`).

### 4.5 SVG 1:1 export

Contour (and optionally seat / rim outlines) in mm units, 50 mm scale bar, "imprimer à 100 %" note.

## 5. How to test it

| # | Test | How | Pass if |
|---|---|---|---|
| T1 | Watertight | `trimesh.load(stl).is_watertight` and `is_winding_consistent`; manifold's own status | true for all test shapes |
| T2 | Volume sanity | volume > 0, no degenerate faces, single connected body | pass |
| T3 | Two shapes | ellipse 50×36 + rounded rectangle 52×34 | both rims match their contours (overlay gap = clearance ± 0.02 mm) |
| T4 | Parameter sweep | clearance 0.1–0.3, bridge 14–22, rim width 2.5–5 | all pass T1 |
| T5 | Slicer check | open the STL in PrusaSlicer / Cura (free): no errors, flat on bed, supports ≈ 0 | pass |
| T6 | Print test (if a printer is available) | print one rim with a real lens | lens clips in without play or forcing; adjust clearance |
| T7 | Browser performance | generation time on a mid-range phone | < 5 s |
| T8 | SVG scale | print the SVG, measure the scale bar | 50.0 ± 0.2 mm |

## 6. Risks

Self-intersecting contours from noisy segmentation break offsets: simplify (`SimplifyPolygon`, Ramer–Douglas–Peucker at 0.05 mm) and enforce a single outer polygon before offsetting.

## 7. Combines with

Strategy 8 (canonical contours), 2 (SVG), 10 (UI: sliders, preview, download), presentation (show a printed front if possible).

## 8. Results log

| Date | Who | Shapes | Watertight | Slicer OK | Print fit | Notes |
|---|---|---|---|---|---|---|
| 2026-10-03 | Codex subagent + parent audit | Asymmetric fixtures and two real pipeline outputs from simulated photos | Yes; single body, positive volume, consistent winding, no degenerate faces | NOT RUN | NOT RUN | Six tests plus measured-contour-to-STL smoke run; see work/strat9/report.md. |
