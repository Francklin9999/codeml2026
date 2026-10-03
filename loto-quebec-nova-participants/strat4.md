# NOVA · Strategy 4: Claim lifecycle tracker ("announced ≠ delivered ≠ validated")

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (differentiator, cheap) |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 step A (corpus); integrates with `facts.yaml` |
| **Rubric lines** | Q01, Q03, Q06, Q08, Q09, Q10; Chronology (proposal / decision / validation with dates); Update after event |
| **Work folder** | `loto-quebec-nova-participants/work/strat4/` |

---

## 1. Context you need

The corpus is built around gaps between what someone *says* and what the accountable person has *validated*: Teams 19 Sept, Sophie: *"« déployé » != « accepté »"*; ACC-303 fix "annoncé pour la prochaine build"; the runbook "n'est pas final"; CR-04 is a draft but its 18k line appears on INV-003; the 22 Oct date was proposed by Boréal (8 Sept) then approved by the committee (10 Sept). The README rule: *"Une correction annoncée n'est pas nécessairement acceptée. Une proposition n'est pas une décision."*

## 2. The idea

Model each tracked item as a small **state machine** and record every transition with date, actor, role and source. Publish a **"claimed but not yet proven"** view: everything between ANNOUNCED and DELIVERED, or DELIVERED and VALIDATED, or PROPOSED and DECIDED.

States: `PROPOSED → DECIDED/APPROVED → ANNOUNCED → DELIVERED → VALIDATED → CLOSED`, plus `DRAFT`, `DEFERRED`, `REJECTED`, `OPEN` (defect), `STALE_CLAIM` (a document asserts a state the evidence does not support).

## 3. Why it could score

It answers Q08, Q09 and Q10 almost directly, gives the chronology criterion its proposal / decision / validation table, and is exactly the structure the live event will touch (a re-test, a new build, a new proposal).

## 4. Implementation plan

### 4.1 Files

```
work/strat4/
  owners.yaml          # who can validate what
  lifecycle.yaml       # items and their transitions (hand-curated, sourced)
  lifecycle.py         # validation rules + rendering
  test_lifecycle.py
  claimed_not_proven.md (generated)
  swimlanes.html        (generated, optional)
```

### 4.2 Accountable owners (validation authority)

```yaml
security: Sophie Lambert
accessibility: Mélissa Gagnon
operations: Olivier Côté
integration: Marc Gervais
data_migration: Camille Beaulieu
architecture: Marc Gervais (équipe architecture)
finance: Amélie Fortin
governance: Comité de direction / chargé de projet (Nicolas Perron depuis le 16 sept)
vendor: Boréal Numérique (Julien Moreau)  # can PROPOSE, ANNOUNCE, DELIVER; never VALIDATE
```

### 4.3 Items and transitions to encode (verify each locator)

| Item | Transitions (date · actor · source) |
|---|---|
| Go-live date | 15 Oct set at kickoff (7 Jul, M01, charter, E01) → **proposed** 22 Oct (8 Sept, Boréal, E05) → **approved** 22 Oct (10 Sept, committee, M04@15:22–15:25), **conditional** (M04@15:27; M06@10:09–10:15; E09) |
| ADR-007 hosting | decided Canada Central (23 Jul, M02@09:10–09:12, ADR-007) → **delivered** migration (26 Aug, Boréal, E03 + Arch v2) → **verified** by architecture team (27 Aug, M03) |
| CR-01 | approved 24k (14 Aug, project committee, CR-01 PDF) → invoiced in INV-002 (31 Aug) → paid |
| CR-04 | **draft** (4 Sept, Boréal) → estimate discussed, "aucune approbation" (10 Sept, M04@15:37–15:40) → **deferred** to phase 2 (24 Sept, scope decision, E10) → invoiced anyway on INV-003 (22 Sept) = **anomaly** → "Facturer du CR-04, non" (26 Sept, M06@10:25) |
| INV-003 | issued 22 Sept, status "En validation" → question from Finance (23 Sept, E07) |
| INT-101 | opened 5 Sept → 401 / token (5 Sept) → intermittent (8 Sept) → fix deployed, 120/120 (17 Sept 14:23, Boréal) → **validated and closed** (17 Sept 16:10, Marc; E12) |
| DATA-401 | opened 2 Sept → fix (idempotency key) → **validated** replay of 15,000 events (9 Sept) → closed (also M04@15:15) |
| PERF-501 | opened 3 Sept → fix 6 Sept → **validated** 620 ms on 50 tries (7 Sept) → closed |
| SEC-210 | opened 12 Sept (blocking) → **delivered** 19 Sept 10:22 (Boréal, E08) → owner refuses closure until re-test 19 Sept 14:05 → re-test planned, **still EN VALIDATION** 26 Sept 15:40 |
| ACC-301 / 302 | fixed by Boréal (14 / 18 Aug) → **validated and closed** by Mélissa (15 / 20 Aug) |
| ACC-303 | opened 17 Sept → reproduced by Boréal 18 Sept → **still OPEN** 26 Sept 11:03, fix **announced** for next build (M06@10:12) |
| OPS-601 runbook | opened 25 Sept (rollback missing + another step per screenshot) → made a go-live condition (26 Sept) → **final version not received** (29 Sept) |
| PM role | Élodie since 7 Jul → Nicolas since 16 Sept (E06, note, Teams) |
| Status report 21 Sept | asserts VERT for security / accessibility → **STALE_CLAIM** |

### 4.4 Rules in `lifecycle.py`

```python
VENDOR = {"Boréal Numérique", "Julien Moreau"}
def check(item):
    for t in item.transitions:
        if t.to in {"VALIDATED", "CLOSED"} and t.actor not in owners_for(item.domain):
            raise RuleError(f"{item.id}: {t.actor} cannot validate {item.domain}")
        if t.to == "DECIDED" and t.authority < COMMITTEE_OR_PM:
            raise RuleError(...)
    return item.transitions[-1].to   # current state
```

Render: (1) a table of current states; (2) the "claimed but not proven" table: item, what is claimed, by whom, what is missing, who must act; (3) optional swimlanes (one row per item, dots per transition, colour by state), as SVG or HTML generated from the YAML.

## 5. How to test it

### 5.1 Expected states at the baseline (unit tests)

| Item | Expected current state |
|---|---|
| Go-live | APPROVED 22 Oct, conditional |
| SEC-210 | DELIVERED (not VALIDATED) |
| ACC-303 | OPEN, fix ANNOUNCED |
| OPS-601 | OPEN, runbook not final |
| CR-04 | DRAFT + DEFERRED; invoiced line = anomaly |
| INT-101, DATA-401, PERF-501, ACC-301, ACC-302 | CLOSED (validated by owner) |
| Hosting | DELIVERED + verified by architecture team |
| Status report | STALE_CLAIM |

### 5.2 Trap tests

- Feed the status report and E11 as transitions → `check()` must refuse to advance SEC-210 or ACC-303 (authority too low).
- Feed "Boréal: ACC-303 corrigé" → ACC-303 becomes DELIVERED, not VALIDATED; condition 2 stays open.

### 5.3 Acceptance

All expected states match; every transition has a locator; the "claimed but not proven" table lists at least SEC-210, ACC-303, OPS-601, CR-04 / INV-003 line.

## 6. Risks

Swimlane rendering can eat time; the table alone carries the points.

## 7. Combines with

Strategy 2 (Q08–Q10 atoms), 3 (authority scale), 5–6 (events are new transitions), 9 (actions come from "what is missing").

## 8. Results log

| Date | Who | Tests | Verdict |
|---|---|---|---|
| | | | |
