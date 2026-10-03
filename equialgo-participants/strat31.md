# EquiAlgo · Strategy 31: Candidate-density covariate-shift weighting

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P2 · **Effort** 4 h · **Depends on** history and candidate features |
| **Rubric** | Hidden-reference accuracy; fixed quota |
| **Work folder** | work/strat31/ |

## 1. Context and evidence

The committee history trains V1–V5, then scores a separate candidate population. The recorded committee CV AUC near .957 is not candidate hidden-reference accuracy. Differences in covariate distribution could make historical fit less useful.

## 2. Idea and novelty

Estimate density ratios for candidate versus history covariates and reweight committee-label training toward candidate-like observations, with clipping and effective-sample-size controls. Unlike strategy 11's group/label reweighing, this corrects train-to-candidate covariate shift without asserting that groups or labels should be independent.

## 3. Rubric

Predictive candidate if observed covariate shift is the main source of transfer error.

## 4. Implementation

Create `work/strat31/shift_weight.py`; cross-fit domain classifier, clip weights at preregistered 5 and 10, report ESS, and fit one candidate only if ESS ≥30% of history.

## 5. Experiment

One preselected candidate may be uploaded if allowed. Adoption requires >94% on confirmed official accuracy; domain AUC or committee metrics are diagnostics only. Stop if weight diagnostics fail; no unbounded leaderboard tuning.

## 6. Risks

Covariate shift assumptions require stable conditional target; weights may explode and amplify noise.

## 7. Combines with

Compare with 21/26, but not simultaneously at first.

## 8. Results log

NOT RUN. No density ratios or hidden-reference results exist.
