# OptiFrame · Strategy 17: Complete printable eyewear (temples, print-in-place hinges, material profiles, size variants)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (beyond the required front; presentation and impact value) |
| **Effort** | 5–6 h |
| **Depends on** | strategy 9 (frame front generator) |
| **Rubric lines** | Generated frame (10: hinges / tenons, printability), Presentation (10), humanitarian usefulness |
| **Differs from 1–10** | Strategy 9 generates the **frame front** with tenons. This extends to a **wearable pair**: temples (arms) sized to the wearer, a hinge design that prints in place or uses a standard pin, and material profiles (PLA / PETG / TPU) that adjust clearances, thicknesses and flex |
| **Work folder** | `optiframe-participants/work/strat17/` |

---

## 1. Context you need

- Palier 3 requires a parametric front with bridge and hinge tenons; the rubric checks *"pont et tenons présents, imprimable sans supports excessifs"*. A full pair is not required, but a real wearable result is compelling for SN-SF's humanitarian use (fablabs, NGOs).
- No face data may be in our datasets (*"Aucune donnée personnelle dans vos jeux de données (visages…)"*): sizing must use parameters entered by the user (e.g. temple length in standard sizes), not face photos.

## 2. The idea

1. **Temples:** parametric arms with standard lengths (e.g. 135, 140, 145 mm), adjustable bend position, a flat profile that prints without supports; optional TPU tips.
2. **Hinges:** two options to test: (a) **print-in-place** knuckle hinge with clearance (0.3–0.4 mm) printed flat; (b) holes for a **standard pin / small screw** or a piece of filament used as the pin (no hardware needed).
3. **Material profiles:** PLA (stiff, brittle), PETG (tougher, slightly flexible), TPU (flexible parts only): each profile sets rim thickness, lip size, lens clearance and hinge clearance.
4. **Size variants:** child / adult presets (bridge, temple length, rim width).
5. **Print plate:** export a single STL / 3MF with front + two temples laid flat and oriented for strength (layer lines along the temple length).

## 3. Why it could score

Showing a printed, wearable pair (or at least a printed front + temple with a working hinge) is a powerful presentation moment and demonstrates printability beyond the minimum.

## 4. Implementation plan

### 4.1 Files

```
work/strat17/
  temples.js            # 2D profile → extrusion (manifold-3d), length/bend parameters
  hinges.js             # print-in-place knuckle / pin-hole variants
  materials.json        # per-material clearances and thicknesses
  plate.js              # arrange parts on a print plate, export STL / 3MF
  print_log.md          # print settings and results (photos)
```

### 4.2 Hinge geometry (print-in-place, flat)

Alternating knuckles on the front's tenon and the temple's end, a pin cylinder fused to one side, a radial clearance per material (start PLA 0.35 mm, PETG 0.4 mm), with chamfers to avoid bridging failures; test-print a hinge coupon first (5 clearances on one small plate).

### 4.3 Checks

Watertightness and manifoldness (as strategy 9), minimum wall thickness ≥ 1.2 mm (2–3 perimeters with a 0.4 mm nozzle), no overhang > 45° except the hinge's designed clearance.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Mesh validity | all parts watertight, single bodies |
| T2 | Hinge coupon | at least one clearance per material rotates freely after printing, without breaking |
| T3 | Full print (if a printer is available) | front + temples printed without supports; hinge works; lenses clip in |
| T4 | Parameter sweep | all size / material presets generate valid meshes |
| T5 | Slicer | PrusaSlicer / Cura shows no errors; estimated print time and filament logged |

## 6. Risks

No printer at the event: rely on slicer checks and printed coupons made before the hackathon, and say so.

## 7. Combines with

Strategy 9 (front), 10 (UI presets), presentation.

## 8. Results log

| Date | Who | Material | Hinge clearance OK | Print result | Notes |
|---|---|---|---|---|---|
| | | | | | |
