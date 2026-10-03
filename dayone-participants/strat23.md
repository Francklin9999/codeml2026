# DayOne · Strategy 23: Annotation instructions as executable test fixtures

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 schema and evaluator |
| **Work folder** | `dayone-participants/work/strat23/` |

## 1. Context and evidence

The audited DayOne report (`work/shared/report.md`) describes ten evaluator tests and explicitly says the provisional inventory is not an enforced clinical ontology. There is no reviewed gold set to validate the interpretation rules. Strategy 7 proposes consistency rules between fields; this idea instead makes annotation and normalization conventions executable, independently of any clinical inference.

Evidence: [DayOne evaluation audit](work/shared/report.md) (provisional schema; no ground-truth pages).

## 2. Idea and distinction

Create a small catalog of input-output examples for each field type and status: blank, dash, overwritten value, ambiguous date, value with unit, ticked choice, and not-visible crop. Store expected parsed form and status in YAML, run them through schema and normalization code, and show examples inline in annotator guidance. This prevents documentation and code from diverging. It does not add clinical plausibility checks or tune OCR.

## 3. Rubric relevance

Consistent status assignment directly supports uncertainty handling; stable normalization makes accuracy scores comparable across extraction strategies.

## 4. Implementation steps

Under `work/strat23/`, add `conventions.yaml`, `validate_conventions.py`, and `examples.md`. Each rule must specify an observable input pattern, expected status/value, and a “do not infer” note. Add fixtures to `work/shared/tests/` only after agreement with current schema behavior. Never include patient identifiers.

## 5. Proposed experiment

Run 40 examples (five cases across eight representative field categories) through both the fixture validator and current normalization path. Baseline: existing behavior without a catalog. Adopt if all normative examples agree and two reviewers independently classify ≥95% of a separate 40-example set; kill if conventions require assumptions unsupported by visible evidence. Thresholds are proposed, not measured.

## 6. Risks

Overly rigid examples can obscure legitimate variation. Keep unresolved readings explicit; do not turn examples into clinical advice or automatic treatment recommendations.

## 7. Combinations

Complements strategies 1, 6, 7, 18, 21, and 22 by clarifying which outputs are comparable.

## 8. Results log

NOT RUN. No convention fixtures have been approved.
