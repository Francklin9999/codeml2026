# NOVA · Strategy 2: Nuance-atom answer grading + dual blind answering

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 step A (extracted corpus); nothing else |
| **Rubric lines** | Q01–Q10 = **50 pts** (each 0 / 3 / 5 for accuracy and nuance), Evidence (10) |
| **Work folder** | `loto-quebec-nova-participants/work/strat2/` |

---

## 1. Context you need

The 10 graded questions (from `README.txt` in the zip):

| Q | Question |
|---|---|
| Q01 | Approved go-live date, and with what caveat? |
| Q02 | Why did the date change, and what is the current state of the original cause? |
| Q03 | Who approved the change and when? Distinguish proposal and approval. |
| Q04 | Who is responsible for the project and since when? |
| Q05 | Authorised contract amount and how it is computed? |
| Q06 | What is wrong with INV-003? Amount concerned and treatment to plan. |
| Q07 | Where must production data be hosted? Which proof confirms the implementation? |
| Q08 | Is security accepted? Distinguish delivery and validation. |
| Q09 | Is accessibility complete? What remains to fix? |
| Q10 | The three go-live conditions; missing runbook work from its screenshot. |

Reading rules in the README that define "nuance": a proposal is not a decision; an announced fix is not necessarily accepted; a recent file date does not guarantee accurate information; attachments duplicated as separate files are not independent confirmations; a historical screenshot alone does not prove a defect is still open; separate authorised, invoiced and paid; say when information is missing, never invent.

## 2. The idea

The gap between 3 and 5 points is nuance. Make it measurable: for each question, list the **atoms** a 5-point answer must contain and the **anti-atoms** that lose points. Have **two independent answerers** (two people, or two LLM sessions with different prompts and no access to the atoms) answer blind, grade both automatically against the atoms, then reconcile and run an adversarial review.

## 3. Why it could score

Most teams will get the headline facts (22 Oct, 204k, Nicolas). Points will be lost on the planted traps. A checklist turns trap-avoidance into a repeatable test, reusable after every live-event drill (strategy 6).

## 4. Implementation plan

### 4.1 Files

```
work/strat2/
  nuance_atoms.yaml      # the scoring proxy (shared with strategies 1, 6, 9)
  prompts/answerer_A.md  # neutral prompt
  prompts/answerer_B.md  # different framing ("audit the project as a skeptical PMO")
  answers_A.md  answers_B.md
  grade.py
  answers_final.yaml     # consumed by strategy 1's site
  adversarial_review.md
```

### 4.2 Step A: write the atoms

Format:

```yaml
Q01:
  atoms:
    - {id: Q01.date,        text: "22 octobre 2026",                              must_cite: ["M04@15:22"]}
    - {id: Q01.approved,    text: "approuvée le 10 septembre par le comité",      must_cite: ["M04@15:25"]}
    - {id: Q01.conditional, text: "conditionnelle / pas un go automatique",       must_cite: ["M04@15:27", "M06@10:15", "E09#body"]}
    - {id: Q01.conditions,  text: "trois conditions (SEC-210, ACC-303, runbook)", must_cite: ["M06@10:09"]}
  anti_atoms:
    - "15 octobre est la date actuelle"
    - "go-live confirmé / garanti"
```

Seed table (from analysis §7.1.4; **verify every locator** in the extracted text before trusting it):

| Q | Required atoms | Anti-atoms |
|---|---|---|
| Q01 | 22 Oct 2026; approved 10 Sept by the steering committee; conditional, not an automatic go; the 3 conditions | "15 Oct"; "go-live confirmed" |
| Q02 | INT-101 connector (HTTP 401 after a secret change, expired service token, then intermittent errors) consumed the margin and became the critical path; Boréal proposed moving the date (E05); **cause resolved**: fix validated 17 Sept, 120/120 searches (E12, ticket); date not moved back, no decision to do so | "connector still open" (register R-01 is stale) |
| Q03 | **Proposed** by Julien Moreau (Boréal) on 8 Sept, E05 says "il s'agit d'une proposition de notre part", repeated at the committee; **approved** 10 Sept by the steering committee, decision stated by Élodie Caron (PM at the time), no objection (Sophie, Marc, Olivier, Nicolas) | "Boréal decided"; "approved by Nicolas on 15 Sept" |
| Q04 | Nicolas Perron **since 16 Sept 2026** (E06, transition note, Teams 16 Sept); Élodie Caron before, since 7 July | "Élodie Caron" (Plan v2 still names her) |
| Q05 | **204,000 $ = 180,000 $ initial maximum + 24,000 $ CR-01** (approved 14 Aug, project committee); CR-04 (18k) is a draft, excluded; context: invoiced 186k, paid 132k; ORION invoice excluded | "180,000 $"; "222,000 $"; counting INV-778 |
| Q06 | 18,000 $ line "Optimisation interface mobile – CR-04"; CR-04 never approved (draft; "aucune approbation" 10 Sept; deferred 24 Sept; "Facturer du CR-04, non" 26 Sept); contract requires written approved change **before execution and invoicing**; treatment: hold the 18k line, process the 36k milestone-3 line normally, request a corrected invoice or credit note | "pay INV-003"; "reject the whole invoice" with no nuance |
| Q07 | **Canada Central** (ADR-007, decided 23 July, accepted; M02 09:06–09:12); Boréal declared migration complete 26 Aug (E03) with Architecture v2 (25 Aug); **verified by the architecture team** (M03); E03's attachment is Architecture v2, so not an independent confirmation | "East US"; E03 + Arch v2 presented as two independent proofs |
| Q08 | **No.** SEC-210 fix delivered / deployed 19 Sept (E08, ticket, Teams); security validation pending, ticket EN VALIDATION, re-test planned (26 Sept 15:40); "déployé != accepté"; status report "VERT" and Alex's draft are wrong | "security accepted / complete" |
| Q09 | **No.** ACC-301 and ACC-302 closed and validated 15 and 20 Aug; **ACC-303 OPEN**, high priority: focus trapped between "Nom" and "Commentaire", "Enregistrer" unreachable with Tab (Chrome and Edge); blocking per Mélissa (M06 10:05); fix only announced for the next build | "accessibility complete" |
| Q10 | (1) SEC-210 security validation; (2) ACC-303 closure; (3) runbook approval including rollback (M06 10:09); **from `OPS-601_runbook.png`: step 4 rollback = TODO and step 5 post-deployment functional validation = À compléter**; Olivier still had no final version on 29 Sept | step 5 missing (only visible in the PNG) |

### 4.3 Step B: blind answers

- Answerer A and B receive: the extracted corpus (strategy 1), the question list, the instruction "for each answer: one-line answer, then nuance bullets, then sources as `file + locator`". They do **not** see `nuance_atoms.yaml`.
- If using LLMs, use two different models or two prompts, and paste the screenshot transcriptions (the model may not see images).
- Save as `answers_A.md`, `answers_B.md` with a fixed structure (`## Q01` …).

### 4.4 Step C: `grade.py`

```python
# For each Q: atom coverage, anti-atom hits, locator presence.
# Matching: normalised substring + synonym list per atom (e.g. "22 oct", "22 octobre", "2026-10-22").
# Optional: an LLM judge for fuzzy matches, but every MISS is confirmed by a human.
report[q] = {
  "coverage": hits / len(atoms),
  "anti_hits": [...],
  "locators_found": n_locators,
  "cross_source": n_distinct_files >= 2,
  "predicted_score": 5 if coverage == 1 and not anti_hits else (3 if coverage >= 0.5 else 0),
}
```

Print a table for A, B and the final version side by side.

### 4.5 Step D: reconcile and adversarial review

1. Merge the best of A and B into `answers_final.yaml` (fields: `short`, `nuance[]`, `sources[{file, locator}]`, `fact_ids[]`).
2. Any atom both answerers missed = likely trap: re-read its sources and add a line to `adversarial_review.md`.
3. A third reader tries to argue each final answer down from 5 to 3 ("which nuance is missing?", "is this source stale?", "is that a proposal or a decision?") and writes the argument; fix or justify.
4. Mark any atom that is our inference rather than a documented fact as *"interprétation de l'équipe"* in the answer.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Every atom has ≥ 1 `must_cite` locator that exists in strategy 1's `locators.jsonl` | 100% |
| T2 | `grade.py` on `answers_final.yaml` | coverage 100% for all 10 Qs, 0 anti-atoms |
| T3 | Evidence criterion | ≥ 3 answers with file + locator, ≥ 2 of them citing **distinct, non-duplicate** sources (check with strategy 10) |
| T4 | Format | each answer starts with a one-line answer ≤ 30 words |
| T5 | Disagreement analysis | list of atoms missed by A or B, each explained |

**Stop condition:** two consecutive adversarial passes find nothing new.

## 6. Risks and guardrails

- The seed atoms come from a draft; an atom with a wrong locator would teach us a wrong answer. T1 is mandatory.
- Long answers bury the key point. Keep "answer first, nuance second, sources third".

## 7. Combines with

Strategy 1 (answers rendered in the site), 4 (Q08–Q10 atoms come from the lifecycle states), 6 (re-grade after each drill event), 10 (independence of sources).

## 8. Results log

| Date | Who | Version graded | Coverage per Q | Anti-atoms | Verdict |
|---|---|---|---|---|---|
| | | | | | |
