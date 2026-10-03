# NOVA · Strategy 15: Multi-project reuse (the bonus): a project-agnostic schema tested on a second mini-project

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (bonus, only after the scored work is solid) |
| **Effort** | 4–5 h |
| **Depends on** | strategies 1, 3, 4 (schema and rules); 11 helps (automatic extraction) |
| **Rubric lines** | challenge bonus ("comparer plusieurs projets, réutiliser certaines connaissances d'un projet à l'autre"); Use (10) via demonstrated generality |
| **Differs from 1–10** | Strategies 1–10 are tailored to NOVA. This proves the approach **transfers**: same schema, same authority and lifecycle rules, applied to a second project, plus a reusable "lessons learned" base |
| **Work folder** | `loto-quebec-nova-participants/work/strat15/` |

---

## 1. Context you need

- `consignes.pdf` bonus: *"comparer plusieurs projets, réutiliser certaines connaissances d'un projet à l'autre, générer automatiquement un briefing exécutif ou produire un dossier permettant de comprendre rapidement les décisions et leurs preuves."* The README rubric does not score it directly.
- The corpus contains a hint of another project: `INV-778_Projet_ORION.pdf` (a 41k invoice from the same vendor for "Migration données – projet ORION"). It is a distractor for NOVA but a seed for a second project.
- Facts about NOVA must come from the corpus; a second project must be clearly **labelled as a synthetic demo** if we create it.

## 2. The idea

1. Separate the system into a **project-agnostic core** (ledger schema, authority scale, lifecycle states, diff engine, brief template) and **project data**.
2. Write a small **synthetic second project** ("ORION", 10–15 short documents we author ourselves, labelled fictional) with deliberately different traps (e.g. a change request approved by the wrong body, a vendor claiming acceptance, a stale budget sheet).
3. Run the same pipeline; show cross-project views: vendor Boréal's behaviour across projects (claims of delivery vs validations), recurring risk patterns, lessons learned ("Boréal declares fixes done before owner validation: always wait for owner sign-off").

## 3. Why it could score

It is the only bonus explicitly listed, it demonstrates that the design is not a one-off, and it gives a strong closing slide. Keep it strictly secondary.

## 4. Implementation plan

### 4.1 Files

```
work/strat15/
  core/                    # schema.py, authority.yaml, lifecycle rules, brief template (moved from strategies 1/3/4)
  projects/nova/           # pointers to NOVA ledger
  projects/orion_demo/     # our synthetic mini-corpus, each file headed "PROJET FICTIF DE DÉMONSTRATION"
  cross_project.py         # vendor view, lessons learned, comparison table
  lessons_learned.yaml
```

### 4.2 Steps

1. Refactor: the NOVA build must still produce exactly the same output after moving shared logic into `core/` (regression test on the generated pages' text).
2. Author ORION documents (meeting notes, 3 tickets, a CR, an invoice, an email) with timestamps and locators in the same formats.
3. Build ORION's ledger (manually or with strategy 11) and its brief.
4. Cross-project page: vendor claims vs owner validations per project; average time from "delivered" to "validated"; recurring contradiction types (stale plans, status reports).
5. `lessons_learned.yaml`: pattern, evidence in each project, recommended control.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Regression | NOVA outputs identical before / after the refactor |
| T2 | Generality | ORION built with **zero** code changes in `core/` (only data) |
| T3 | Trap handling | ORION's planted traps resolved correctly by the same rules (unit tests) |
| T4 | Labelling | every ORION page shows "projet fictif de démonstration"; no ORION fact appears in NOVA answers |

## 6. Risks

Time drain and confusion with NOVA facts. Hard cap at the effort estimate; keep ORION visibly separate.

## 7. Combines with

Strategy 1, 3, 4, 11; presentation (strategy 19) closing slide.

## 8. Results log

| Date | Who | Regression OK | Code changes for ORION | Traps resolved | Notes |
|---|---|---|---|---|---|
| | | | | | |
