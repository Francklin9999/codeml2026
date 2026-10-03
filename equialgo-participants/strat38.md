# EquiAlgo · Strategy 38: Candidate prediction leakage and order audit

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 2 h · **Depends on** frozen candidate files and validator |
| **Rubric** | Valid hidden-reference accuracy measurement |
| **Work folder** | work/strat38/ |

## 1. Context and evidence

The validated V1 baseline has 4,000 rows and 1,600 grants. A leaderboard score is meaningful only if the prediction artifact is generated from authorized inputs, correctly ordered, and not contaminated by hidden outcomes.

## 2. Idea and novelty

Audit candidate generation for target leakage: compare features used to fit against the supplied history/candidate schema, trace IDs and file hashes, and confirm no leaderboard feedback was expanded into row labels. Unlike strategy 20's generator reverse-engineering, this is an artifact lineage audit before external scoring.

## 3. Rubric

Protects the validity and integrity of an otherwise high leaderboard score.

## 4. Implementation

Create `work/strat38/leakage_checklist.md`; review code/data lineage, ID joins, target columns, ignored local files, exact row order, and top-k count. Reviewer signs before upload.

## 5. Experiment

Audit V1 CSV and each finalist. Pass only if all candidate IDs map one-to-one, 1,600 labels are positive, no hidden-label source exists, and a second reviewer reproduces the file hash. Any failure blocks upload and invalidates associated score.

## 6. Risks

Audits can miss subtle leakage; a high score alone is not evidence of process integrity.

## 7. Combines with

Strategies 24, 36, 37; apply before every final upload.

## 8. Results log

NOT RUN. No finalist audit has been signed.
