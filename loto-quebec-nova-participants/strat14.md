# NOVA · Strategy 14: Stakeholder and accountability map (RACI derived from the corpus)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 step A (corpus) |
| **Rubric lines** | Brief & actions (10: owners for the 3 go-live conditions), Chronology (10: who has authority to decide / validate), Q03, Q04 |
| **Differs from 1–10** | Strategy 4 hard-codes who validates what. This makes **people and their accountabilities** a first-class, sourced view (who decides, who validates, who delivers, who must be informed), which the action register and the authority rules then reuse |
| **Work folder** | `loto-quebec-nova-participants/work/strat14/` |

---

## 1. Context you need

People appearing in the corpus (verify roles from sources):

| Person | Role in the corpus (to source) |
|---|---|
| Élodie Caron | project manager from 7 July (charter, M01, E01) until 16 Sept (E06, transition note) |
| Nicolas Perron | project manager since 16 Sept 2026 (E06, transition note, Teams 16 Sept); chairs the 26 Sept committee |
| Marc Gervais | architecture / integration (M02, M04 15:06, INT-101 validation, E12) |
| Sophie Lambert | security (M02, SEC-210 owner, "déployé != accepté") |
| Mélissa Gagnon | accessibility / QA (ACC tickets, M04, M06) |
| Olivier Côté | operations (runbook, OPS-601, M04, M06) |
| Camille Beaulieu | data migration (DATA-401, M04 15:15) |
| Amélie Fortin | Finance (E07, INV-003 validation) |
| Alex Deschamps | communications (E11, Teams 15 Sept) |
| Julien Moreau | vendor Boréal Numérique (proposals, deliveries) |
| Steering committee | decision body (M04, M06) |

## 2. The idea

Build a **RACI matrix** per subject (go-live date, security, accessibility, operations / runbook, integration, data migration, budget / invoices, scope / change requests, communications), where every letter is backed by a source:
- **R**esponsible: who does the work (often Boréal);
- **A**ccountable: who validates / decides (owner or committee);
- **C**onsulted, **I**nformed.

Add a "**who can say yes to what**" table: committee decides dates and scope; owners validate their domain; Finance releases payments; the vendor can only propose and deliver.

## 3. Why it could score

The brief and action criteria need owners; the chronology criterion needs authority. A sourced accountability map answers both and prevents the classic error of treating Boréal's "c'est réglé" as a validation. It also makes the live event easier: when a message arrives, we immediately know whether its author can change anything.

## 4. Implementation plan

### 4.1 Files

```
work/strat14/
  people.yaml        # person → roles with sources and validity dates (Élodie until 16 Sept, etc.)
  raci.yaml          # subject → R/A/C/I with sources
  build_raci.py      # renders a matrix (HTML / Markdown / xlsx sheet)
  who_can_approve.md
```

### 4.2 Building it

1. For each person, list every mention with role cues ("chargée de projet", "côté exploitation", "Finances", "Sécurité"); record `valid_from` / `valid_until` (role changes over time: PM transition on 16 Sept).
2. For each subject, assign R/A/C/I only where a source supports it; otherwise mark "proposé par l'équipe" (our recommendation) explicitly.
3. Render: matrix with clickable sources; a timeline strip for the PM role change; a short "who can approve what" table.
4. Export `people.yaml` for strategies 3 and 4 (authority scale and validators), and for strategy 9's owner column.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Source coverage | every R/A/C/I letter has a source or is labelled as our recommendation |
| T2 | Time validity | queries "who was PM on 10 Sept?" → Élodie; "on 26 Sept?" → Nicolas |
| T3 | Condition owners | each of the 3 go-live conditions has an Accountable person (Sophie, Mélissa, Olivier) with a source |
| T4 | Vendor guard | Boréal never appears as Accountable for validation |
| T5 | Reuse | strategy 9's action owners and strategy 4's validators read from `people.yaml` without manual edits |

## 6. Risks

Inventing roles. If a role is only implied (e.g. Alex's function), say "rôle déduit" and show the cue.

## 7. Combines with

Strategy 3 (authority), 4 (validators), 9 (owners), 6 (live event: "can the author of this message decide?").

## 8. Results log

| Date | Who | People mapped | Unsourced cells | Notes |
|---|---|---|---|---|
| | | | | |
