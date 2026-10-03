# NOVA · Strategy 9: One-page brief + action register (commitment vs recommendation)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 2 (final answers), 4 (states); renders into strategy 1's site |
| **Rubric lines** | Brief & actions (10), Use (10), deliverables 1 and 2 |
| **Work folder** | `loto-quebec-nova-participants/work/strat9/` |

---

## 1. Context you need

- Deliverable 1: *"Un brief de reprise d'une page maximum : responsable, date approuvée et conditions, portée, budget, situation des factures et priorités."*
- Deliverable 2: actions with *"responsable proposé ou confirmé, preuve, et échéance connue ou « à confirmer »"*, and *"Distinguez une recommandation de votre équipe d'un engagement déjà documenté."*
- Rubric: 5 pts for the 5 themes on one page; 5 pts for linking the **3 go-live conditions** to actions, owners and due dates (known or "à confirmer").

## 2. The idea

Produce the two artefacts someone taking over NOVA would actually use on Monday: a strict **one-page brief** and an **action register** in which every line says whether the owner is confirmed or proposed, whether the due date is known, which evidence supports it, and whether it is a documented commitment or our recommendation.

## 3. Why it could score

The checklist is explicit, and most teams will blur commitment vs recommendation or exceed one page. Both are mechanically testable.

## 4. Implementation plan

### 4.1 Files

```
work/strat9/
  brief.md.j2  brief.html  brief.pdf
  actions.yaml  actions.html
  check_brief.py
```

### 4.2 Brief content (verify every line against the ledger)

| Theme | Content |
|---|---|
| Responsable | Nicolas Perron, chargé de projet depuis le 16 sept 2026 (E06, note de transition) |
| Date et conditions | 22 oct 2026, approuvée le 10 sept par le comité de direction (M04), **conditionnelle** à : validation sécurité SEC-210, fermeture ACC-303, approbation du runbook avec rollback (M06, E09) |
| Portée | Phase 1 : SSO, création / suivi de demandes, pièces jointes, workflow, tableau de suivi, rapports standards (+ CR-01 rapports avancés). Mobile avancé (CR-04) reporté en phase 2, non approuvé |
| Budget et factures | Autorisé 204 000 $ (180 000 + CR-01 24 000). Facturé 186 000 $ ; payé 132 000 $ (INV-001, INV-002). INV-003 (54 000 $) en validation : retenir la ligne CR-04 de 18 000 $, traiter la ligne jalon 3 de 36 000 $. INV-778 = projet ORION, hors NOVA |
| Priorités | 1) les 3 conditions ; 2) correction INV-003 ; 3) corriger les documents périmés (plan v3, R-01, rapport de statut) ; 4) communication : ne pas annoncer le 22 comme un go garanti |
| Incertitudes | dates des re-tests et de la prochaine build non documentées ; statut de l'étape 5 du runbook après le 25 sept inconnu |

### 4.3 Action register seed (`actions.yaml`)

```yaml
- id: A-01
  action: "Re-test sécurité de SEC-210 et décision d'acceptation"
  linked_condition: 1
  owner: "Sophie Lambert"
  owner_status: documented
  due: "à confirmer (re-test « planifié » le 26 sept)"
  due_status: unknown
  origin: commitment
  evidence: ["SEC-210#2026-09-26T15:40", "M06@10:02"]
- {id: A-02, action: "Livrer le correctif ACC-303", linked_condition: 2, owner: "Boréal (Julien Moreau)", owner_status: documented, due: "prochaine build (date à confirmer)", due_status: unknown, origin: commitment, evidence: ["ACC-303#2026-09-26T11:03", "M06@10:12"]}
- {id: A-03, action: "Re-tester et fermer ACC-303", linked_condition: 2, owner: "Mélissa Gagnon", owner_status: proposed, due: "à confirmer", due_status: unknown, origin: recommendation, evidence: ["M06@10:05"]}
- {id: A-04, action: "Fournir le runbook final : rollback (étape 4) + validation fonctionnelle post-déploiement (étape 5)", linked_condition: 3, owner: "Boréal (équipe ops relancée par Julien)", owner_status: documented, due: "à confirmer ; Olivier voulait le runbook « quelques jours avant »", due_status: unknown, origin: commitment, evidence: ["M06@10:12", "M04@15:12", "OPS-601#2026-09-29", "OPS-601_runbook.png#step4"]}
- {id: A-05, action: "Approuver le runbook (go exploitation)", linked_condition: 3, owner: "Olivier Côté", owner_status: documented, due: "avant le 22 oct", due_status: known, origin: commitment, evidence: ["M06@10:07"]}
- {id: A-06, action: "Retenir la ligne CR-04 de 18 000 $ ; demander une facture corrigée ou une note de crédit", owner: "Amélie Fortin + Nicolas Perron", owner_status: proposed, due: "à confirmer", due_status: unknown, origin: recommendation, evidence: ["E07#body", "E10#body", "CONTRAT_Boreal_NOVA.pdf#p1"]}
- {id: A-07, action: "Mettre à jour le plan v3 (22 oct) et fermer R-01 au registre", owner: "Nicolas Perron", owner_status: proposed, due: "à confirmer", due_status: unknown, origin: recommendation, evidence: ["M04@15:25", "Note_transition_Elodie_16sept.txt"]}
- {id: A-08, action: "Corriger le rapport de statut et le message d'Alex", owner: "Nicolas Perron / Alex Deschamps", owner_status: proposed, due: "avant toute communication", due_status: unknown, origin: recommendation, evidence: ["E11#body", "E09#body"]}
- {id: A-09, action: "Comité go / no-go avant le 22 oct", owner: "Nicolas Perron", owner_status: proposed, due: "à confirmer", due_status: unknown, origin: recommendation, evidence: ["E09#body", "M06@10:15"]}
```

Note on A-07: updating the plans was *requested* (M04 15:25 "On doit mettre les plans et communications à jour", transition note) but no owner or date is documented, so it stays a recommendation with a proposed owner.

### 4.4 Rendering

Generate the brief from the ledger (strategy 1) with a Jinja2 template; print CSS for A4 / Letter (`@page { size: A4; margin: 12mm }`, 10–10.5 pt font). Render `actions.html` as a sortable table with columns: action, condition, owner (+ badge confirmed/proposed), due (+ badge known/à confirmer), origin (badge commitment/recommendation), evidence links.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | One page | headless print to PDF (e.g. Chrome `--headless --print-to-pdf`, or WeasyPrint) has exactly 1 page at ≥ 10 pt |
| T2 | Theme checklist (`check_brief.py`) | the 5 themes present, each with ≥ 1 source |
| T3 | Condition linkage | each of conditions 1–3 has ≥ 1 action with owner and due (or "à confirmer") |
| T4 | Origin audit | every `origin: commitment` has evidence where someone commits; all others are `recommendation` |
| T5 | Cold read | a newcomer reads the brief for 2 min and answers "what blocks go-live?" and "how much remains authorised but not invoiced?" correctly: 18,000 $ if every invoiced line counts (204k − 186k), **36,000 $ once the unapproved 18,000 $ CR-04 line is excluded** (204k − 168k), which is the correct treatment; the brief must make this distinction visible |
| T6 | Post-event regeneration | after a strategy 5 event, the brief regenerates and still fits one page |

## 6. Risks

Overflowing one page. Cut prose, keep tables; put details behind links.

## 7. Combines with

Strategy 1, 2, 4, 5 (state_t1 brief), 6 (drills check the brief update).

## 8. Results log

| Date | Who | Pages | Checks passed | Verdict |
|---|---|---|---|---|
| | | | | |
