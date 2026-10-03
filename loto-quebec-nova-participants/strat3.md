# NOVA · Strategy 3: Authority × time contradiction resolver

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (differentiator) |
| **Effort** | 4–5 h |
| **Depends on** | strategy 1 (`facts.yaml`) |
| **Rubric lines** | Chronology & contradictions (10); supports Q01, Q02, Q04, Q08, Q09; reused by the live event (10) |
| **Work folder** | `loto-quebec-nova-participants/work/strat3/` |

---

## 1. Context you need

The Chronology criterion has two 5-point findings: (a) distinguish proposal, decision and validation with dates and sources; (b) explain **at least two contradictions by the authority or the date of the facts, one of them in a plan or a risk register**. The corpus README warns: *"Analysez le contenu et son autorité; une date de fichier récente ne garantit pas une information exacte."*

Known contradictions in the corpus (verified while reading):

| # | Claim A | Claim B | Expected resolution |
|---|---|---|---|
| C1 | `Plan_Projet_NOVA_v3_12sept.xlsx`: go-live 15 Oct **(plan)** | M04 10 Sept: 22 Oct approved | Committee outranks a derived plan; Teams 15 Sept: "le plan projet n'a visiblement pas encore été corrigé" |
| C2 | `Registre_Risques_29sept.xlsx` R-01 "Retard du connecteur interne" = Ouvert **(register)** | INT-101 closed and validated 17 Sept (ticket, E12, M05) | Cell H2 says "Suivi au 9 septembre 2026": information date 9 Sept despite the 29 Sept file date |
| C3 | `Rapport_Statut_21sept.pdf`: security / accessibility VERT | SEC-210 EN VALIDATION; ACC-303 OPEN | The report says it was prepared before detailed ticket checks; owners' ticket statuses outrank a status report |
| C4 | Teams 22 Sept, Julien: advanced mobile was in the initial scope | Charter, contract, M01 note, scope decision 24 Sept, E10 | Contract scope + formal decision outrank a vendor's belief |
| C5 | Plan v2: PM = Élodie Caron | E06, transition note, Teams 16 Sept: Nicolas since 16 Sept | Later formal transition |
| C6 | E11 draft (Alex): "sécurité et accessibilité complétées" | tickets | Draft based on the stale status report |
| C7 | Personal notes: "15 oct encore date? probablement" | M04 | Anonymous, no authority |

## 2. The idea

Give every claim an **authority level** and an **information date** (`info_as_of`, distinct from the file date). Compute "currently valid" per subject with an explicit rule, and generate each contradiction's explanation in plain French from the rule. The same engine later decides what a live event overrides and what it does not.

## 3. Why it could score

It produces the chronology deliverable systematically, with reasons the jury can check, and it makes the live-event update principled instead of improvised.

## 4. Implementation plan

### 4.1 Files

```
work/strat3/
  authority.yaml        # scale + one-line justification per level
  resolver.py
  test_resolver.py
  contradictions.md     # generated
```

### 4.2 Authority scale (justify it in the deliverable)

```yaml
levels:   # higher number wins
  9: committee_decision     # M04, M06 decisions, CR approval by committee
  8: contract               # signed contract, approved CR document
  7: accountable_owner_validation  # Sophie (security), Mélissa (accessibility), Olivier (ops), Marc (integration), Camille (data), Amélie (finance)
  6: pm_formal              # PM emails / notes / published minutes
  5: owner_ticket_status    # ticket status set by its owner
  4: vendor_statement       # Boréal emails / comments ("fix déployé", "migration complétée")
  3: derived_document       # plans, risk register, status report (copies of other facts)
  2: chat                   # Teams messages (unless quoting a decision)
  1: anonymous_note
```

Edge cases to encode explicitly: a vendor statement can establish **delivery** but never **validation**; a derived document can establish nothing that contradicts a higher source with an earlier or equal information date; a chat message *quoting* a committee decision gets the committee's authority only if the decision exists in the corpus.

### 4.3 Resolver rule

```python
def current_value(subject, claims):
    cands = [c for c in claims if c.subject == subject and c.type != "proposal"]
    top = max(c.authority for c in cands)
    best = max((c for c in cands if c.authority == top), key=lambda c: c.info_as_of)
    # Later but lower-authority conflicting claims are reported, not applied:
    flags = [c for c in cands if c.info_as_of > best.info_as_of and c.value != best.value]
    return best, flags

def explain(a, b, winner):
    reason = ("autorité supérieure" if winner.authority > loser.authority
              else "information plus récente")
    return f"{loser.source} ({loser.info_as_of}) dit « {loser.value} » ; " \
           f"remplacé par {winner.source} ({winner.info_as_of}) : {reason}."
```

Add `info_as_of` to the ledger entries of derived documents (e.g. R-01 → 2026-09-09, status report → before 21 Sept ticket checks).

### 4.4 Generate the contradictions page

For each subject with ≥ 2 conflicting values, emit: claim A, claim B (file, locator, quote), winner, reason, and "what should be fixed" (e.g. "Mettre à jour le plan v3", "Fermer R-01 dans le registre"). Output Markdown, consumed by strategy 1's site.

## 5. How to test it

### 5.1 Unit tests (`test_resolver.py`)

| Test | Expected |
|---|---|
| `current_value("go-live")` | 22 Oct (M04), flags Plan v3 as stale |
| `current_value("INT-101")` | closed 17 Sept; R-01 reported stale because `info_as_of = 2026-09-09` |
| `current_value("SEC-210")` | delivered, not validated |
| `current_value("ACC-303")` | open |
| `current_value("PM")` | Nicolas Perron since 2026-09-16 |
| `current_value("scope.mobile")` | CR-04 not approved, deferred to phase 2 |
| Each of C1–C7 | resolved with the expected winner and a reason string |

### 5.2 Perturbation tests

| Injected claim | Expected behaviour |
|---|---|
| Committee, 2 Oct: "go-live moved to 29 Oct" | resolver switches to 29 Oct; 22 Oct becomes superseded |
| Boréal, 2 Oct: "SEC-210 accepted" | **not applied** (vendor cannot validate); flagged |
| Plan v4, 3 Oct: "go-live 15 Oct" | not applied; flagged as stale derived document |
| Sophie, 2 Oct: "SEC-210 re-test OK" | SEC-210 validated; ACC-303 and runbook unchanged |

### 5.3 Acceptance / kill

- **Adopt** if all unit and perturbation tests pass with ≤ 5 special cases in the code.
- **Kill:** if more special cases are needed, keep a hand-written contradictions table (the points are in the explanation) and use the authority scale only as documentation.

## 6. Risks

Over-engineering. The jury reads explanations, not code. Keep the rule simple and print reasoning in plain French.

## 7. Combines with

Strategy 1 (data and page), 4 (state per item), 5–6 (events go through the same rule), 2 (Q01/Q02/Q04 nuance).

## 8. Results log

| Date | Who | Tests passed | Special cases | Verdict |
|---|---|---|---|---|
| | | | | |
