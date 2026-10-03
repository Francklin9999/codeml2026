# NOVA · Strategy 5: Bitemporal event store with frozen baseline and diff

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (foundation for the live event) |
| **Effort** | 4–6 h |
| **Depends on** | strategy 1 (`facts.yaml`); uses rules from 3 and 4 if available |
| **Rubric lines** | Update after the event (10), Use (10), deliverable 4 ("état actualisé, changements par rapport au baseline, preuves et actions touchées. Conservez la version initiale.") |
| **Work folder** | `loto-quebec-nova-participants/work/strat5/` |

---

## 1. Context you need

During the final presentation a new piece of information is given. The rubric's update criterion: (a) distinguish **problem status, prior decision and new proposal**; (b) **keep the baseline** and produce sourced impacts and actions **without inventing approvals or closing other conditions**. The baseline = what is known at 30 Sept 2026 09:00.

## 2. The idea

Store the memory as an **append-only log of events**, each with two times: `valid_time` (when it is true in the project) and `record_time` (when we learned it). The baseline is `state(record_time ≤ 2026-09-30T09:00-04:00)`, frozen to `baseline.json` with a SHA-256 hash. A live event is appended; `state_t1` is recomputed; `diff.py` reports what changed, what is impacted, and what deliberately did **not** change.

## 3. Why it could score

"Keep the baseline" becomes true by construction; the diff is automatic and sourced; guardrails (no invented approval, no closing other conditions) are enforced by code instead of memory under stage pressure.

## 4. Implementation plan

### 4.1 Files

```
work/strat5/
  events/                 # one YAML per event; baseline events generated from facts.yaml
    0000_baseline_*.yaml
    1001_live_event.yaml  # written during the demo
  store.py                # load, fold, freeze
  diff.py                 # baseline vs state_t1
  guardrails.py
  test_store.py
  baseline.json  baseline.sha256
  out/state_t1.json  out/diff.md  out/diff.html
```

### 4.2 Event schema

```yaml
event_id: 1001
record_time: 2026-10-0XTHH:MM-04:00   # when the jury gave it to us
valid_time: 2026-10-0X                # when it happened in the project (if stated)
subject: SEC-210
kind: status_change        # new_claim | status_change | decision | proposal | correction
statement: "Le re-test sécurité de SEC-210 a échoué : l'identifiant du dossier manque toujours."
actor: Sophie Lambert
authority: accountable_owner_validation
source: "Événement live (présentation finale)"
affects_hint: [Q01, Q08, Q10]          # optional; diff.py computes the real list
```

### 4.3 Folding events into a state

```python
def state(as_of_record_time):
    evs = sorted(e for e in events if e.record_time <= as_of_record_time)
    s = State()
    for e in evs:
        guardrails.check(e, s)     # raises on forbidden transitions
        s.apply(e)                 # uses strategy 3's resolver + strategy 4's lifecycle rules
    return s
```

`freeze_baseline()` writes `baseline.json` (sorted keys) and its SHA-256; `store.py verify` recomputes and compares.

### 4.4 Guardrails (`guardrails.py`)

1. A `proposal` never changes an approved value (approved date stays, proposal listed separately).
2. A vendor `delivery` never sets VALIDATED.
3. An event about subject X cannot change the state of any other go-live condition.
4. An approval requires an approving authority (committee or PM for governance; owners for validation).
5. If the event is ambiguous (e.g. "ça devrait être bon"), the state change is `UNCONFIRMED` and an action "confirmer auprès de <owner>" is generated.

### 4.5 `diff.py` output (Markdown + HTML)

1. **Ce qui change:** changed facts (old → new, source).
2. **Statut du problème / décision antérieure / nouvelle proposition:** three explicit lines (the rubric's wording).
3. **Réponses touchées:** Q01–Q10 whose cited facts changed, with the new wording.
4. **Actions touchées:** new, modified or closed actions with owner and due date ("à confirmer" if unknown).
5. **Contradictions:** new or resolved.
6. **Ce qui ne change pas (volontairement):** the other conditions, approved date if only proposed, budget, etc.
7. Baseline hash shown to prove it is untouched.

## 5. How to test it

### 5.1 Property tests (`test_store.py`, use `hypothesis` if available)

| Property | Check |
|---|---|
| Baseline immutability | after appending any event, `sha256(baseline.json)` unchanged |
| Replay determinism | rebuilding from the log twice gives identical `state_t1` |
| Reversibility | removing the live event gives back exactly the baseline |
| No silent edits | events directory is append-only (test fails if a baseline event file changed) |

### 5.2 Guardrail scenarios

| Event | Expected |
|---|---|
| Boréal proposes 29 Oct | approved date stays 22 Oct; 29 Oct shown as proposal; action: committee decision |
| Boréal: "ACC-303 corrigé dans la build 14" | ACC-303 = DELIVERED; condition 2 open; action: Mélissa re-test |
| Sophie: "re-test SEC-210 OK" | SEC-210 = VALIDATED; ACC-303 and runbook unchanged; go-live still conditional |
| Committee approves CR-04 on date D | authorised = 222k from D; INV-003 mobile line payable only for work after D (flag for Finance) |
| Olivier receives runbook v2 | runbook = DELIVERED, not approved; step 5 status unknown → action |

### 5.3 Timing

From receiving a typed event to regenerated deliverable: **< 10 minutes** including human review. Measure in three drills with strategy 6.

### 5.4 Acceptance / kill

- **Adopt** when all property and guardrail tests pass and the timing target is met 3 times.
- **Fallback at hour 16:** copy `facts.yaml` → `facts_t1.yaml`, edit by hand, produce the diff table manually; still never touch the baseline file.

## 6. Risks

Building a database instead of a deliverable. YAML files + 300 lines of Python are enough.

## 7. Combines with

Strategy 3 and 4 (state computation), 6 (drills), 1 (versions page), 2 (re-grade affected answers), 9 (brief regenerated for `state_t1`).

## 8. Results log

| Date | Who | Tests | Drill timing | Verdict |
|---|---|---|---|---|
| | | | | |
