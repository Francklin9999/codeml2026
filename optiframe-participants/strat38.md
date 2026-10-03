# OptiFrame · Strategy 38: Lens-edge bevel and silhouette convention audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 2 metrology pipeline; several physical lenses |
| **Work folder** | `optiframe-participants/work/strat38/` |

## 1. Context and evidence

Current measurements use synthetic polygons with explicit outer boundaries; the measured maximum error is 0.312796 mm on a blurred synthetic case. The report says real lenses, bevels, and edge definition are not validated. Strategy 8 proposes calliper bias calibration. This proposal defines which visible physical edge corresponds to the intended outline across lens profiles before fitting any correction.

Evidence: [metrology report](work/strat2/report.md) records synthetic analytic boundaries; physical bevel behavior remains untested.

## 2. Idea and distinction

On a small, consented set of non-identifying sample lenses, capture the same lens from both sides and under several backlight levels. Annotate top silhouette, bottom silhouette, bevel line, and apparent rim line separately, then compare each against a consistent calliper convention. Quantify which edge the current detector tracks and how that choice changes A/B. Do not train a generalized correction from a handful of lenses.

## 3. Rubric relevance

Reduces definitional measurement error and makes limitations clear for thick or strongly beveled lenses.

## 4. Implementation steps

Add a physical annotation protocol and `work/strat38/edge_convention.py`. Store only random lens IDs and dimensions; do not include names, prescriptions, or identifying photographs. Use overlays for review and separate this study from calibration fitting.

## 5. Proposed experiment

Study eight lenses across at least three visible edge-profile categories, three captures per side; baseline current detected contour versus one agreed calliper convention. Adopt an edge-selection rule only if median A/B absolute deviation improves by ≥25% in leave-one-lens-out evaluation and no category worsens by >0.3 mm. Proposed thresholds, not measured.

## 6. Risks

Small samples may not cover materials or lens powers; calliper convention and edge labels require independent agreement.

## 7. Combinations

Pairs with strategies 2, 8, 21, and 36; it supplies edge-definition evidence before bias calibration rather than duplicating calibration.

## 8. Results log

NOT RUN. No physical lens edge convention study exists.
