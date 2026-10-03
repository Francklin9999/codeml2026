# DayOne · Strategy 13: Longitudinal cross-visit reconciliation (using a woman's earlier pages as priors)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (schema), strategy 10 (linking), an extractor |
| **Rubric lines** | Extraction (30), Uncertainty (20), Conversational review (20: re-digitisation and updates), Patient linking (10) |
| **Differs from 1–10** | Strategy 7 checks consistency **within** one record. This checks and improves extraction **across pages and visits of the same woman**: stable facts must not change, cumulative tables must only grow, and re-photographed pages should be diffed against what is already validated |
| **Work folder** | `dayone-participants/work/strat13/` |

---

## 1. Context you need

- The registry is longitudinal: the *Grossesse actuelle* page has a visit table (up to 9 columns) filled over months; the same booklet is photographed again at each visit. Brief task 7: *"si un registre est rephotographié, afficher le dossier existant et laisser la sage-femme choisir quoi mettre à jour."*
- Some facts are **stable** across the booklet (DDR, expected delivery date, blood group / Rh, height, gravidity / parity at enrolment); others are **append-only** (visit columns: once a past visit is validated, it should not change); others are **new** (the latest visit).

## 2. The idea

When a page arrives for a linked patient:
1. Align its extraction with the patient's **validated record**.
2. Classify each field: *unchanged* (matches validated value), *new* (empty before, filled now: e.g. a new visit column), *conflict* (a validated value now reads differently).
3. **Use the validated record as a prior**: for unchanged fields, a near-match (edit distance 1) is very likely a misread of the same value → keep the validated value and raise confidence; for conflicts on stable fields, ask the midwife; for new fields, normal extraction and review.
4. Track per-field provenance (which capture, which date, who validated).

## 3. Why it could score

At the second visit, most of the page is already known. Reusing it avoids re-asking the midwife about 50 fields, catches misreads cheaply, and makes the re-digitisation flow the brief requires concrete.

## 4. Implementation plan

### 4.1 Files

```
work/strat13/
  field_classes.yaml   # stable / append-only / new / free for each schema key
  reconcile.py         # validated record + new extraction → per-field decision
  provenance.py        # value history per field
  eval_13.md
```

### 4.2 Decision rules

| Field class | New extraction vs validated | Action |
|---|---|---|
| stable | equal | keep; confidence ↑ |
| stable | edit distance ≤ 1 (likely misread) | keep validated; log |
| stable | different | `À_RÉVISER` with both values: [Garder l'ancien] [Prendre le nouveau] |
| append-only (past visit column) | equal or ≤ 1 edit | keep validated |
| append-only | different | `À_RÉVISER` (someone may have corrected the paper) |
| new (empty before) | any | normal status / confidence logic |

### 4.3 Cross-page constraints

DDR on *Grossesse actuelle* must equal DDR elsewhere; delivery date on page 4 must be after the last visit; newborn weight on the post-partum newborn page should match the delivery page. Feed violations to strategy 7 / 9.

### 4.4 Simulation data

Simulate visits from the specimen: for each patient, create "visit k" versions of page 3 by blanking visit columns after k (keep the GT), then extract each version in sequence (with degradations from strategy 4).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Field accuracy at visit k > 1 | higher with reconciliation than without (same extractor) |
| T2 | Questions per page at visit k > 1 | ≥ 50% fewer than at visit 1 |
| T3 | Conflict detection | injected changes to stable fields (simulated paper corrections) are always surfaced, never silently overwritten |
| T4 | Provenance | for any field, the history shows capture IDs, dates and validator |

## 6. Risks

Over-trusting the prior could hide a genuine correction made on paper; that is why stable-field differences always go to the midwife.

## 7. Combines with

Strategy 10 (linking gives the patient), 9 (diff UI), 8 (versions in the store), 7 (cross-page rules).

## 8. Results log

| Date | Who | Visit | Accuracy (with / without) | Questions / page | Notes |
|---|---|---|---|---|---|
| | | | | | |
