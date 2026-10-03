# DayOne · Strategy 34: Table-row association benchmark

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 zones; strategy 2 registration |
| **Work folder** | `dayone-participants/work/strat34/` |

## 1. Context and evidence

The specimen PDF has dense repeated tables and `pdftotext -layout` misaligns columns; strategy 1 proposes PyMuPDF word coordinates and table zones. Yet the evaluator has no reviewed ground truth, so current evidence does not establish row association accuracy (`work/shared/report.md`). This proposal isolates row/column binding as a benchmark instead of building a new OCR engine.

Evidence: [DayOne evaluation audit](work/shared/report.md) notes no reviewed ground-truth pages.

## 2. Idea and distinction

Build a small adversarial benchmark where field values are identical but table row positions vary: empty rows, wrapped text, repeated dates, faint separators, and values near column boundaries. Score whether each recognized token is assigned to the right row and column independent of character recognition. Compare geometric center-in-cell against nearest separator and graph-based assignment.

## 3. Rubric relevance

Correct character recognition is useless if attached to the wrong visit; explicit association metrics expose this error separately.

## 4. Implementation steps

Implement `work/strat34/association.py`, a synthetic layout generator, and confusion report. Keep text fixtures fictitious. Add an assignment confidence and “ambiguous row” output, not a forced choice.

## 5. Proposed experiment

Generate 200 synthetic table instances with controlled skew and row gaps, plus 40 reviewed specimen crops once available. Baseline: nearest cell center. Adopt a method if synthetic exact row/column accuracy reaches ≥98% and reviewed-set accuracy exceeds baseline by ≥5 points without increasing confident wrong assignments; otherwise keep the ambiguity flag. Proposed thresholds, not measured.

## 6. Risks

Synthetic rows may not reproduce handwritten overlap; no conclusion about phone OCR follows from generated cases alone.

## 7. Combinations

Pairs with strategies 1, 2, 4, 21, 24, and 33.

## 8. Results log

NOT RUN. No association benchmark has been built.
