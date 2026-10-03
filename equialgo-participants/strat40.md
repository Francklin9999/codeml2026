# EquiAlgo · Strategy 40: Final candidate selection against confirmed accuracy target

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 2 h · **Depends on** confirmed metric and score receipts |
| **Rubric** | Hidden-reference leaderboard accuracy |
| **Work folder** | work/strat40/ |

## 1. Context and evidence

The user confirms >94% leaderboard accuracy against the hidden reference is required. Current V1 baseline has a validated 4,000-row/1,600-grant file; its leaderboard score is unrecorded. Existing committee CV AUC and simulated H1–H5 outputs do not answer this target.

## 2. Idea and novelty

Use a single final decision record that compares the V1 baseline and preregistered candidates by returned official accuracy, hash, quota, and upload conditions. No surrogate metric can substitute; if none exceeds 94%, record the goal as unmet rather than promoting the least-bad result.

## 3. Rubric

Makes the final choice traceable to the actual user requirement and prevents simulation metrics from being misrepresented.

## 4. Implementation

Create `work/strat40/decision.md`; list metric definition, benchmark source, baseline score, candidate score, receipts, validator state, and dissent/limitations. Keep all hidden labels inaccessible.

## 5. Experiment

Confirm metric is accuracy and score is from authorized leaderboard; independently verify file and receipt. Select only candidates scoring >94%; if no such result is returned within allowed attempts, clearly state “not beaten.”

## 6. Risks

Leaderboard conditions may differ from final judging; confirm version and submission constraints.

## 7. Combines with

Strategies 36–39; final step after predictive candidates are tested.

## 8. Results log

NOT RUN. No candidate leaderboard accuracy or final selection is available.
