# DayOne · Strategy 33: Field dependency map for review navigation

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 schema; strategy 9 review UI |
| **Work folder** | `dayone-participants/work/strat33/` |

## 1. Context and evidence

Strategy 7 checks cross-field consistency; strategy 9 proposes asking about uncertain values. Current evaluation confirms only a provisional schema and ten tests, with no reviewed labels (`work/shared/report.md`). This idea adds a navigational map of relationships so a reviewer can see which fields are linked by a form structure, without asserting medical rules or changing a value.

Evidence: [DayOne evaluation audit](work/shared/report.md) confirms only a provisional schema/evaluator foundation.

## 2. Idea and distinction

Represent field relationships as typed edges: same table row, same checkbox group, repeated visit, or shared date reference. When one field is uncertain, highlight adjacent evidence and linked entries in the same document section. Keep relationship types descriptive and avoid inferred clinical dependencies. Unlike strategy 7's validator, the map organizes review but never flags a value as medically inconsistent.

## 3. Rubric relevance

Improves field-level human verification and reduces navigation errors in dense multipage forms.

## 4. Implementation steps

Add a static graph definition in `work/strat33/field_map.yaml`, a validator, and UI component. Require every edge to point to schema keys and a documented printed-form relationship. Use synthetic fixtures only.

## 5. Proposed experiment

On 24 synthetic review tasks, compare finding a specified neighboring field with and without highlights. Baseline: current unlinked form view. Adopt if median navigation time drops ≥20%, with zero incorrect edits to linked fields; kill if users interpret visual grouping as inferred clinical causality. Proposed threshold, not measured.

## 6. Risks

Visual grouping can imply relationships stronger than the form supports. Label each connection as layout-only and keep validation rules elsewhere.

## 7. Combinations

Complements strategies 7, 9, 17, 28, and 31 without replacing their logic.

## 8. Results log

NOT RUN. No field graph or navigation study exists.
