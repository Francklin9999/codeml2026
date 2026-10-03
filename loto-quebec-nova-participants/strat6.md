# NOVA · Strategy 6: Live-event impact playbook and timed drills

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h + 20 min per drill |
| **Depends on** | strategy 2 (atoms), 4 (states); 5 recommended |
| **Rubric lines** | Update after the event (10), Use & uncertainty (10) |
| **Work folder** | `loto-quebec-nova-participants/work/strat6/` |

---

## 1. Context you need

The event is unknown until the final presentation. The rubric wording narrows it: *"distinguer statut du problème, décision antérieure et nouvelle proposition; conserver le baseline et produire les impacts/actions sourcés sans inventer d'approbation ni fermer d'autres conditions."* The most plausible events concern the three go-live conditions (SEC-210, ACC-303, runbook) and a possible new date proposal. Open question for the organisers: in which form will the event arrive (document, email, verbal) and how much time do we get?

## 2. The idea

Pre-compute an **impact map** for every plausible event family, prepare a spoken script, and run **timed blind drills**: one person writes a surprise event, another integrates it while the clock runs, a third grades it with the rubric and a guardrail checklist.

## 3. Why it could score

10 points are decided in a few minutes on stage. Improvisation leads to the two classic errors (inventing an approval, closing an untouched condition). Rehearsal makes the right answer routine.

## 4. Implementation plan

### 4.1 Files

```
work/strat6/
  impact_map.md         # the table below, completed with sources
  event_bank/           # 12–15 written events in realistic formats (email, Teams, verbal)
  drills/NN_event.md  drills/NN_result.md  drills/NN_grade.md
  spoken_script.md
  guardrail_checklist.md
```

### 4.2 Impact map (complete each cell with sources)

| Event family | Problem status | Prior decision that still stands | New proposal | Answers affected | Actions (owner, due) |
|---|---|---|---|---|---|
| SEC-210 re-test **fails** | SEC-210 reopened / rework | 22 Oct approved, conditional | maybe a new date from Boréal | Q01, Q08, Q10, brief | Boréal fix (due à confirmer); Sophie re-test; Nicolas: convene committee; hold communications |
| SEC-210 re-test **passes** | condition 1 met | 22 Oct still conditional on ACC-303 + runbook | — | Q08, Q10, brief | update register R-02; do not declare go |
| Boréal delivers ACC-303 fix | DELIVERED, not validated | — | — | Q09, Q10 | Mélissa re-test; condition 2 still open |
| Mélissa validates ACC-303 | condition 2 met | — | — | Q09, Q10, brief | close ticket; update brief |
| Runbook v2 received | received ≠ approved; rollback present? step 5? | — | — | Q10 | Olivier review and approval |
| Boréal proposes a new date (e.g. 29 Oct) | depends on cause | **22 Oct stays approved** until committee decides | 29 Oct = proposal | Q01, Q02, Q03 | committee meeting; check contract end 31 Oct |
| Committee approves a new date | — | 22 Oct superseded | — | Q01, Q03, brief, plan | update plans and comms; conditions unchanged unless stated |
| Committee approves CR-04 | — | phase-2 deferral superseded | — | Q05, Q06 | authorised 222k from approval date; INV-003 mobile line handling with Amélie |
| Corrected INV-003 / credit note | INV-003 compliant | — | — | Q05, Q06 | Amélie releases the 36k line |
| PM change or absence | — | — | — | Q04, brief | reassign actions |
| Data residency incident / question | — | ADR-007 stands | — | Q07 | architecture check |
| New document repeating a stale fact (e.g. plan still 15 Oct) | — | committee decision wins | — | contradictions | ask the owner to correct |
| Ambiguous message ("ça devrait être bon") | UNCONFIRMED | unchanged | — | none until confirmed | confirm with the accountable owner |

### 4.3 Event bank

Write each event as it might arrive: a short email with headers, a Teams line, a sentence read aloud by a juror. Mix in noise (an irrelevant detail, a misleading word like "réglé"). Keep the bank hidden from the integrator.

### 4.4 Drill protocol

1. Writer picks an event (from the bank or a new one) and hands it over.
2. Integrator starts a timer; uses strategy 5 (or a manual copy of the ledger) to produce: updated state, diff vs baseline, affected answers, actions with owners and due dates, explicit "not changed" list.
3. Integrator delivers the 60-second spoken summary (`spoken_script.md` template: *Ce qui change… Ce qui ne change pas… Ce qui reste une proposition… Actions et responsables… Ce que nous ne savons pas.*).
4. Grader scores with the rubric's two findings (0/5/10) and the guardrail checklist: no invented approval; no other condition closed; baseline preserved and shown; every impact sourced (event or corpus); unknown dates marked "à confirmer".

## 5. How to test it

| Metric | Target |
|---|---|
| Number of drills | ≥ 5, covering ≥ 4 different families |
| Time to integrate (event → updated deliverable + spoken summary) | < 10 min |
| Guardrail violations | 0 in the last 3 drills |
| Rubric score per drill | 10/10 in the last 3 drills |

Record every drill in `drills/`. After each failure, update `impact_map.md` or strategy 5's guardrails.

## 6. Risks

Rehearsing only "nice" events. Include at least one ambiguous message and one that tempts closing two conditions at once.

## 7. Combines with

Strategy 5 (tooling), 2 (re-grade affected answers), 3 (authority rule), 9 (brief regeneration).

## 8. Results log

| Drill | Event family | Time | Score | Violations | Lesson |
|---|---|---|---|---|---|
| | | | | | |
