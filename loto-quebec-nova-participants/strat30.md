# NOVA · Strategy 30: Claims-to-answer coverage and contradiction regression

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (answer integrity) |
| **Effort** | 3–5 h |
| **Depends on** | final answers, fact IDs, source locators |
| **Rubric lines** | all ten factual answers; nuance |
| **Work folder** | work/strat30/ |

## 1. Context and evidence

The 10 known questions contribute half the rubric, with scores depending on accuracy and nuance. Strategy 2 defines nuance atoms, and strategy 11 verifies extracted quotations. This proposal mechanically checks whether every answer clause is supported and whether required qualification atoms remain after editing.

## 2. Idea and novelty

Create a trace matrix at clause level: answer sentence → fact ID → locator → required nuance/anti-atom. Add a regression snapshot so edits cannot remove caveats such as conditional approval or “deployed is not accepted.” Unlike strategy 2's grading design, it is a release-time completeness check across the actual rendered answer text.

## 3. Rubric

Reduces unsupported detail and accidental loss of important caveats in final answers.

## 4. Implementation

Add `work/strat30/answer_trace.csv` and a checker. Each clause gets one or more fact IDs; an editor manually confirms semantic entailment. Use exact expected strings only for controlled labels, not brittle full-sentence matching.

## 5. Experiment and decision

Baseline: Q01–Q10 draft answers and strategy 2's atom list. Require 100% factual clauses linked, all designated nuance atoms present, and zero anti-atoms in two independent reviews. If any fails, remove/rewrite the claim before export; do not infer 5-point scores from checker success.

## 6. Risks

Mechanical linkage cannot prove entailment; atom lists can omit important nuance or encode an incorrect interpretation.

## 7. Combines with

Strategies 2, 7, 11, 24 and 25; run on the final rendered version.

## 8. Results log

NOT RUN. No clause trace, checker, or independent answer review exists.
