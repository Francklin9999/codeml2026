# NOVA · Strategy 12: Simulated jury: multi-persona rubric scoring and follow-up question generation

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (cheap, catches gaps before the real jury does) |
| **Effort** | 3 h + 20 min per run |
| **Depends on** | a first version of the deliverable (strategy 1 or any format) |
| **Rubric lines** | all six lines, as an evaluation tool |
| **Differs from 1–10** | Strategy 2 grades the **10 answers** against fact checklists. This one grades the **whole deliverable** against all twelve 5-point findings of the rubric, the way a jury would, and generates the follow-up questions the team must be ready for |
| **Work folder** | `loto-quebec-nova-participants/work/strat12/` |

---

## 1. Context you need

The rubric (README in the zip) has 50 points for Q01–Q10 and five practical criteria worth 0, 5 or 10, each made of **two 5-point findings**:
- Evidence: ≥ 3 answers with a retrievable file + locator; ≥ 2 of them crossing distinct sources.
- Chronology: proposal / decision / validation with dates and sources; ≥ 2 contradictions explained by authority or date, one in a plan or risk register.
- Brief & actions: 5 themes on one page; 3 go-live conditions → actions, owners, due dates.
- Use & uncertainty: the jury can open the deliverable and find a proof; the team shows its search and states limits during the follow-up question.
- Update: problem status vs prior decision vs new proposal; baseline kept, sourced impacts, no invented approval, no other condition closed.

## 2. The idea

Run a **simulated jury** before every milestone:
1. **Three personas** (LLM sessions or teammates role-playing): *a Loto-Québec PMO lead* (precision, nuance), *an auditor* (evidence, sources, money), *an operations manager taking over the project* (usefulness, actions).
2. Each persona receives only what the real jury gets (the exported deliverable + the README rubric), must **find a proof for 3 random questions themselves**, and scores each of the 12 findings 0/5 with a one-line justification.
3. Each persona writes the **5 hardest follow-up questions** it would ask; the team prepares answers (strategy 19).

## 3. Why it could score

Teams usually discover missing rubric items at the presentation. A scripted mock jury, run 3 times during the 24 hours, turns the rubric into a regression test.

## 4. Implementation plan

### 4.1 Files

```
work/strat12/
  personas.md              # persona prompts / role cards
  findings_checklist.yaml  # the 12 findings with pass conditions and where to look
  run_jury.py              # optional: automates LLM personas over the exported HTML/Markdown
  runs/run_YYYYMMDD_HHMM.md  # scores, justifications, follow-up questions
  followups_bank.md        # deduplicated questions + our prepared answers
```

### 4.2 Persona protocol

- Input: the export (HTML pages converted to text with links preserved, or screenshots for a human run), the rubric, nothing else.
- Task 1: answer "Where is the proof that SEC-210 is not accepted?" and two random others, citing what they clicked.
- Task 2: score the 12 findings (0 or 5), justify each in one line.
- Task 3: list 5 follow-up questions, rated by difficulty.
- Task 4 (update criterion): given a sample event, judge our diff output against the two update findings.

### 4.3 Automating with an LLM (optional)

`run_jury.py` concatenates the export's pages (respecting a token budget), runs the three personas with temperature 0.3, and aggregates scores. Treat the output as a smoke test: a human reviews every "0" before acting on it.

### 4.4 Using the results

Every finding scored 0 by ≥ 2 personas becomes a task with an owner. Every follow-up question goes into `followups_bank.md` with a prepared answer and the exact place in the deliverable to show.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Sanity | on a deliberately broken export (brief removed, links broken), the jury scores the right findings 0 |
| T2 | Agreement | persona scores agree on ≥ 9 of 12 findings (otherwise the checklist wording is ambiguous: fix it) |
| T3 | Progress | run 3 (late) scores ≥ run 1 on every finding; target 60/60 on the practical criteria |
| T4 | Follow-ups | ≥ 15 distinct follow-up questions banked, each with an answer and a location |

## 6. Risks

LLM personas can be lenient. Calibrate with T1, and keep one human run before the final presentation.

## 7. Combines with

Strategy 2 (answers), 19 (presentation rehearsal uses the follow-up bank), 6 (update criterion drills).

## 8. Results log

| Run | Date | Practical score /60 (avg of personas) | Findings at 0 | New follow-ups | Fixes assigned |
|---|---|---|---|---|---|
| | | | | | |
