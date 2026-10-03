# EquiAlgo · Strategy 37: Hidden-score result provenance and blind check

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 2 h · **Depends on** authorized leaderboard results |
| **Rubric** | Valid comparison with reported 94% benchmark |
| **Work folder** | work/strat37/ |

## 1. Context and evidence

The user identifies 94% as leaderboard accuracy against the hidden reference; no result is yet present in the repository. Candidate files must all preserve the exact 4,000-row order and 1,600 grants.

## 2. Idea and novelty

Have one person upload a hash-locked CSV and another independently verify the returned score, metric name, attempt ID, and correspondence to the file hash. Unlike the shared CSV validator, this verifies the external score association without collecting hidden labels.

## 3. Rubric

Ensures the claimed >94% result, if obtained, is tied to the correct candidate and actual accuracy metric.

## 4. Implementation

Create `work/strat37/score_receipts.md`; record organizer interface, metric text, candidate SHA-256, upload time, score and second-person check. Keep credentials private.

## 5. Experiment

For baseline and every permitted candidate upload, require exact match of score receipt and local hash. Candidate passes ultimate gate only if independently logged accuracy is strictly >94%; otherwise no beat claim. One discrepancy invalidates the comparison until resolved.

## 6. Risks

Leaderboard versions/rules may change; screenshots may omit metric context. Verify with organizer if ambiguous.

## 7. Combines with

Strategy 36 tournament and strategy 40 final decision; do not infer labels from aggregate score.

## 8. Results log

NOT RUN. No upload receipt or accuracy result exists.
