# NOVA · Strategy 16: Evidence-backed corrected status report (official RAG vs reality)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 4 (states) or the curated ledger |
| **Rubric lines** | Chronology & contradictions (10), Brief (10), Q08, Q09; example question "Si je devais reprendre le projet demain matin, que devrais-je savoir?" |
| **Differs from 1–10** | Strategy 3 explains contradictions one by one. This produces a **ready-to-send replacement status report** in the same format as the official one, dimension by dimension, with the evidence that justifies each colour and a diff against the official 21 Sept report |
| **Work folder** | `loto-quebec-nova-participants/work/strat16/` |

---

## 1. Context you need

- `04_Documents_projet/Rapport_Statut_21sept.pdf` presents the project as green. Its text layer is scrambled by `pdftotext -layout`; the likely table (to **verify visually** on the rendered page) is: Échéancier VERT "Cible 22 octobre"; Budget VERT "Sous le plafond contractuel"; Sécurité VERT "Correctif SEC-210 livré"; Accessibilité VERT "Correctifs appliqués"; Exploitation JAUNE "Runbook à finaliser". Its own management comment says it was prepared before the last detailed ticket checks.
- E11 (21 Sept): Alex drafts "NOVA est au vert. La sécurité et l'accessibilité sont complétées…" based on that report.
- E09 (27 Sept): Nicolas asks not to communicate 22 Oct as a guaranteed go.

## 2. The idea

Rebuild the status report **as of 30 Sept 09:00** with explicit, sourced criteria for each colour, then show it side by side with the official one:

| Dimension | Official (21 Sept) | Corrected (30 Sept) | Why (sources) |
|---|---|---|---|
| Échéancier | VERT | JAUNE: 22 Oct approved but conditional on 3 open items; contract ends 31 Oct (9 days of margin) | M04, M06, E09, contract |
| Budget / factures | VERT | JAUNE: within 204k authorised, but INV-003 contains an unapproved 18k CR-04 line under validation | INV-003, E07, CR-04, contract |
| Sécurité | VERT | ROUGE (blocking for go-live): SEC-210 fix delivered 19 Sept, security validation pending | SEC-210, M06 10:02 |
| Accessibilité | VERT | ROUGE (blocking): ACC-303 open, "Enregistrer" unreachable by keyboard | ACC-303, M06 10:05 |
| Exploitation | JAUNE | ROUGE (blocking): runbook incomplete (rollback TODO, post-deployment validation à compléter) | OPS-601 + screenshot, M06 10:07 |
| Intégration | (not in report) | VERT: INT-101 closed 17 Sept | E12, ticket |
| Données | (not in report) | VERT: DATA-401 closed 9 Sept | ticket, M04 15:15 |

(The colours are **our assessment**; define the colour rules first and label the report "évaluation de l'équipe de reprise".)

## 3. Why it could score

It turns several contradictions into one artefact a manager immediately understands, prevents the wrong communication (E11), and is a strong visual for the presentation.

## 4. Implementation plan

### 4.1 Files

```
work/strat16/
  rag_rules.yaml          # explicit colour rules per dimension
  build_status.py         # ledger/states → corrected report (HTML/PDF) + diff vs official
  official_transcription.md  # hand-checked transcription of the 21 Sept PDF
  status_30sept.html
```

### 4.2 Colour rules (example)

- ROUGE: a go-live condition not met with no validated fix, or a blocking defect open.
- JAUNE: on track but conditional, or an unresolved financial / contractual issue.
- VERT: closed and validated by the accountable owner.
Apply them mechanically from strategy 4's states so the report regenerates after the live event.

### 4.3 Output

One page: corrected table, a "Ce qui a changé depuis le rapport du 21 sept" column, a recommended communication line (replacement for Alex's draft, consistent with E09), sources as links.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Transcription | official table transcribed by two people independently, identical |
| T2 | Rule determinism | regenerating from states gives the same colours; changing one state (e.g. SEC-210 validated) changes only the security row |
| T3 | Sources | every cell of the corrected column has ≥ 1 source |
| T4 | Labelling | report clearly labelled as the takeover team's assessment, not an official document |

## 6. Risks

Presenting our colours as facts. The label and the explicit rules are the guard.

## 7. Combines with

Strategy 3 (contradiction C3), 4 (states), 9 (brief), 5–6 (regenerated after the event).

## 8. Results log

| Date | Who | Rows differing from official | Sources complete | Notes |
|---|---|---|---|---|
| | | | | |
