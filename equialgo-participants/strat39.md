# EquiAlgo · Strategy 39: Robustness guardrail for a >94% candidate

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 3 h · **Depends on** candidate leaderboard pass |
| **Rubric** | Hidden-reference accuracy; valid exact-budget submission |
| **Work folder** | work/strat39/ |

## 1. Context and evidence

The requested target is strictly above 94% accuracy on the same hidden-reference leaderboard. A single result may be sensitive to a file-generation mistake or leaderboard condition; no score has yet been returned.

## 2. Idea and novelty

When a candidate first exceeds 94%, regenerate it independently from frozen code/configuration and verify predictions byte-for-byte before any optional repeat upload. This is not a new model family or broad uncertainty analysis; it checks the specific candidate artifact supporting the success claim.

## 3. Rubric

Protects the benchmark claim from accidental changes and establishes repeatability of the candidate output.

## 4. Implementation

Create `work/strat39/reproduction.md`; record first file hash, code revision, seed, validator results, and independent regeneration comparison. Request a repeat leaderboard score only if rules permit and the first attempt's status is ambiguous.

## 5. Experiment

Adopt only if independently regenerated file is identical, exact budget/order validation passes, and authorized leaderboard accuracy is >94%. A second upload is optional and bounded; never adjust individual rows from aggregate results.

## 6. Risks

Same code can reproduce the same systematic error. Repetition cannot replace independent hidden-label evaluation.

## 7. Combines with

Strategies 24, 36–38; required before announcing a beat-benchmark result.

## 8. Results log

NOT RUN. No candidate has crossed the threshold or been independently reproduced.
