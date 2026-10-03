# NOVA · Strategy 17: Rebuilt risk register as of 30 Sept + "top 3 risks" answer

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 step A; strategy 4 helps |
| **Rubric lines** | Chronology & contradictions (10: the contradiction "in a plan or a risk register"), Brief & actions (10: priorities), example question "Quels sont les trois principaux risques du projet aujourd'hui?" |
| **Differs from 1–10** | Strategy 3 flags R-01 as stale. This **rebuilds the whole register** as of the reference date (close, update and add risks, with probability, impact, owner, mitigation and sources) and derives a defended top 3 |
| **Work folder** | `loto-quebec-nova-participants/work/strat17/` |

---

## 1. Context you need

`04_Documents_projet/Registre_Risques_29sept.xlsx` (columns: ID, Risque, Probabilité, Impact, Propriétaire, Statut, Mitigation, Commentaire). Known rows (read the full file): R-01 "Retard du connecteur interne" (Moyenne / Élevé, Marc Gervais, **Ouvert**, comment "Suivi au 9 septembre 2026"), R-02 "Validation sécurité incomplète" (Élevée / Élevé, Sophie Lambert, Ouvert, "Re-test de SEC-210 avant go-live"), R-03 "Préparation exploitation incomplète" (Moyenne / Élevé, Olivier Côté, Ouvert, "Finaliser le runbook et le ro[llback]…").

Risks visible in the corpus but possibly absent from the register (verify):
- **ACC-303** keyboard trap, blocking per Mélissa (M06 10:05).
- **INV-003 / CR-04**: unapproved 18k line invoiced; Boréal said at M06 10:24 it had "déjà commencé à regarder quelques ajustements" on mobile → scope creep and payment dispute.
- **Schedule margin**: go-live 22 Oct vs contract period ending 31 Oct (contract PDF; M04 15:18 "le contrat court jusqu'à fin octobre").
- **Communication risk**: stale status report and Alex's draft could announce a guaranteed go (E11, E09).
- **Stale planning documents**: Plan v3 still at 15 Oct (Teams 15 Sept).
- **Knowledge transfer** after the PM change (transition note, "je demeure disponible quelques jours").

## 2. The idea

Produce `Registre_Risques_30sept_reconstruit` with, for each risk: status at 30 Sept (open / closed / new), probability and impact with a **written justification**, owner (sourced or proposed), mitigation, trigger / early-warning signal, due date or "à confirmer", sources, and a change note vs the 29 Sept file. Then rank by a simple score (probability × impact, ties broken by proximity to go-live) to answer "top 3".

## 3. Why it could score

It satisfies the "contradiction in a register" requirement in a constructive way (we don't just say R-01 is stale; we close it with evidence) and gives a defensible answer to a likely follow-up question.

## 4. Implementation plan

### 4.1 Files

```
work/strat17/
  register_30sept.yaml
  build_register.py      # → xlsx sheet (strategy 13) + HTML table + top-3 card
  scoring.md             # probability / impact scale definitions
```

### 4.2 Steps

1. Transcribe the 29 Sept register fully (all rows and cells).
2. For each existing risk, update status from evidence (R-01 → closed 17 Sept, INT-101 validated, E12; R-02 and R-03 still open, sharpened with ticket dates).
3. Add new risks from the list above with sources; mark each new risk "ajouté par l'équipe de reprise".
4. Define the scales (e.g. Probabilité: faible / moyenne / élevée with criteria; Impact: modéré / élevé / bloquant go-live).
5. Compute ranking; write the top 3 in one sentence each, e.g. (to validate) 1) security validation not obtained before 22 Oct, 2) ACC-303 not fixed and re-tested in time, 3) runbook with rollback not approved; and note the financial risk (INV-003) as the top non-schedule risk.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Transcription | all rows of the original file present, two-person check |
| T2 | Evidence | every status change and every new risk has ≥ 1 source |
| T3 | Consistency | risks tied to go-live conditions match strategy 4's states |
| T4 | Top-3 robustness | the top 3 is stable if scores of neighbouring risks change by one level (or the answer says it is a close call) |

## 6. Risks

Overstating our own judgement; keep "added by the takeover team" visible.

## 7. Combines with

Strategy 3 (contradiction C2), 9 (priorities in the brief), 13 (register sheet), 6 (events update risks).

## 8. Results log

| Date | Who | Risks closed / updated / added | Top 3 | Notes |
|---|---|---|---|---|
| | | | | |
