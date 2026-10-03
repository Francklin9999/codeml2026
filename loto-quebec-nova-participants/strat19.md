# NOVA · Strategy 19: Unknowns register and stakeholder question pack ("ce que nous ne savons pas")

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2 h |
| **Depends on** | strategy 1 (ledger) |
| **Rubric lines** | Use & uncertainty (10: "explicite les limites"), Brief & actions (10: "échéances connues ou à confirmer"), README rule "Si une information manque, indiquez-le. N'inventez ni décision, ni échéance, ni approbation." |
| **Differs from 1–10** | The other strategies record what we know. This systematically records **what the corpus does not say**, why it matters, who could answer, and drafts the exact question to send, turning uncertainty into actions instead of guesses |
| **Work folder** | `loto-quebec-nova-participants/work/strat19/` |

---

## 1. Context you need

Gaps already noticed while reading the corpus (verify and extend):

| Unknown | Why it matters | Who can answer |
|---|---|---|
| Date of the SEC-210 security re-test ("planifié", no date) | condition 1, go-live | Sophie Lambert |
| Date / number of the "next build" with the ACC-303 fix | condition 2 | Julien Moreau (Boréal) |
| Whether runbook step 5 (post-deployment functional validation) has progressed since the 25 Sept screenshot | condition 3 | Olivier Côté / Boréal ops |
| Due date for the final runbook (Olivier wanted it "quelques jours avant") | condition 3 | Olivier Côté |
| Who exactly in the architecture team verified the Canada Central migration, and how | Q07 proof strength | Marc Gervais |
| Whether Boréal performed mobile work already (M06 10:24 "on a déjà commencé à regarder quelques ajustements") and on which budget | INV-003 / scope | Julien Moreau, Nicolas Perron |
| Date of the next steering committee / go-no-go | governance | Nicolas Perron |
| Penalties or contract options if go-live slips past 31 Oct | schedule risk | contract owner / legal |
| Whether the plans and the register will be updated, by whom | stale documents | Nicolas Perron |

## 2. The idea

Maintain `inconnues.yaml`: each unknown with its impact on answers / conditions, the evidence showing it is unknown (e.g. "ticket says 'planifié' without a date"), the person who can resolve it (from strategy 14), and a **ready-to-send question** (short French email or Teams message). Show it as a page "Limites et informations incertaines" and link each unknown from the answers and actions that depend on it.

## 3. Why it could score

The Use criterion's second finding requires stating limits during the follow-up question; the README forbids inventing dates or approvals. This page makes our honesty visible and useful (the next person knows exactly whom to ask what).

## 4. Implementation plan

### 4.1 Files

```
work/strat19/
  inconnues.yaml
  questions_to_send.md     # drafted messages, grouped by recipient
  build_unknowns.py        # page + backlinks from answers / actions
```

### 4.2 Steps

1. For each answer (Q01–Q10) and each action, ask "what would make this answer more complete?"; record the gap if the corpus is silent.
2. Mark each unknown `blocking` (affects a go-live condition or a payment) or `informative`.
3. Draft questions grouped by recipient (one message per person), e.g. to Sophie: "Pouvez-vous confirmer la date du re-test de SEC-210 et les critères d'acceptation ?"
4. Link: answer pages show "Information manquante : voir I-03".

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Coverage | every "à confirmer" in the action register points to an unknown entry |
| T2 | Evidence of absence | each unknown cites where the information would be expected and is not |
| T3 | No invention | grep the deliverable for dates or approvals not in the ledger: 0 |
| T4 | Follow-up rehearsal | a teammate asks "what don't you know?"; the answer lists the blocking unknowns in < 30 s |

## 6. Risks

Listing trivia. Keep only unknowns that change an answer, a condition, an action or money.

## 7. Combines with

Strategy 9 (due dates "à confirmer"), 14 (who to ask), 12 and 20 (follow-up questions).

## 8. Results log

| Date | Who | Unknowns (blocking / informative) | Questions drafted | Notes |
|---|---|---|---|---|
| | | | | |
