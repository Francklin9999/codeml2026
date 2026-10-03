# OptiFrame · Strategy 27: Metamorphic invariants for lens/frame geometry

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 9 frame geometry; strategy 2 contour metrics |
| **Work folder** | `optiframe-participants/work/strat27/` |

## 1. Context and evidence

The audited strategy-9 implementation is a Python STL prototype and its tests cover selected shapes and mesh gates; physical validation remains NOT RUN. Strategy 2 measures metric contours and strategy 9 offsets them. This proposal tests mathematical invariants on valid inputs, not malformed-input handling (strategy 26) or browser/server routing (strategies 10 and 19).

Evidence: [STL audit](work/strat9/report.md) documents the tested mesh gates and synthetic-derived input.

## 2. Idea and distinction

Apply translations, rotations, reflections, and uniform scale changes to valid contours and frame parameters, then verify the corresponding output transforms predictably: rigid transforms preserve lengths and area as appropriate, scaling multiplies dimensions and perimeter linearly and area quadratically, and mirroring swaps eye-side orientation without changing intrinsic dimensions. These metamorphic checks do not need independent ground-truth labels for each generated outline.

## 3. Rubric relevance

Tests geometry correctness across transformations without requiring extra labeled contours.

## 4. Implementation steps

Create `work/strat27/metamorphic.py`, seeded contour generators, and invariant report. Include asymmetric and near-degenerate but valid shapes. Verify invariants before and after STL reload, using explicit tolerances and preserving existing examples.

## 5. Proposed experiment

Generate 30 valid contours and five transformed copies each; hold out six asymmetric outlines before tuning. Baseline: current strategy-9 fixture suite. Adopt if length/perimeter invariant deviation is ≤0.05 mm, area deviation ≤0.2%, and eye mirroring preserves A/B while swapping orientation metadata. Proposed criteria, not measured.

## 6. Risks

Floating-point and mesh sampling require tolerances. Metamorphic consistency does not demonstrate contour accuracy or physical fit.

## 7. Combinations

Pairs with strategies 2, 9, 21, 26, and 30.

## 8. Results log

NOT RUN. Current tests cover fixed examples but not these transformed-input invariants.
