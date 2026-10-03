# OptiFrame · Strategy 28: Mesh feature accessibility and inspection report

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 9 Python STL prototype |
| **Work folder** | `optiframe-participants/work/strat28/` |

## 1. Context and evidence

Strategy 9's synthetic-derived mesh passed watertightness, winding, positive volume, one-body, and nondegenerate-face gates, but slicer, print, fit, and hinge compatibility tests are NOT RUN. This proposal expands inspection of intended features and clearances in the mesh, distinct from topology validity and physical print validation.

Evidence: [STL audit](work/strat9/report.md) records five topology gates; feature inspection, slicer, and print remain untested.

## 2. Idea and distinction

Add an STL inspector that samples sections through lens seats, grooves, bridge, and tenons; reports minimum wall thickness, aperture clearance, groove continuity, pin-bore diameter, and left/right symmetry where appropriate. Generate a human-readable dimension sheet alongside the existing topology report. Use geometry fixtures with known analytic dimensions.

## 3. Rubric relevance

Makes a generated frame auditable and catches feature loss that a watertight mesh test cannot detect.

## 4. Implementation steps

Implement `work/strat28/mesh_features.py` under strategy work. Read STL output and source contours, sample cross-sections, and compare measured mesh features to intended parameters. Preserve independent topology checks; mark all assumptions and tolerances.

## 5. Proposed experiment

Inspect 12 meshes from synthetic contours across three rim widths and clearances. Baseline: existing five mesh gates. Adopt if every designed feature is detected, feature dimensions are within ±0.1 mm of intended values, and intentionally removed grooves/bores are caught; kill any metric that yields false confidence on altered meshes. Proposed criteria, not measured.

## 6. Risks

Mesh sampling resolution can miss tiny features, and software inspection cannot establish print strength or fit.

## 7. Combinations

Pairs with strategies 9, 17, 21, 27, and 29.

## 8. Results log

NOT RUN. Existing report covers topology, not this feature inspection.
