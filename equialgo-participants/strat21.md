# EquiAlgo · Strategy 21: Asymmetric group-conditional label-noise model

| | |
|---|---|
| **Status** | IN PROGRESS (sensitivity fits; EM and official evaluation pending) · **Priority** P1 · **Effort** 6 h · **Depends on** candidate data, V1 baseline CSV |
| **Rubric** | Hidden-reference accuracy under authorized leaderboard scoring |
| **Work folder** | work/strat21/ |

## 1. Context and evidence

Committee labels are not known to equal the hidden reference. Historical committee CV AUC near .957 measures committee prediction only. The five current candidates select 1,600/4,000; no leaderboard score or reference label has been reported. The user reports a 94% best score, but the evaluation result is not yet independently recorded.

## 2. Idea and novelty

Fit a latent merit probability while allowing committee label flips at different rates by region and by observed committee label. Estimate parameters under explicit sensitivity bounds; unlike strategy 11's marginal label reweighing, this models asymmetric, group-conditional corruption and predicts the latent clean label.

## 3. Rubric

Candidate mechanism for improving accuracy if committee decisions are a noisy proxy for the reference.

## 4. Implementation

Create `work/strat21/noisy_logit.py`. Enumerate plausible flip-rate bounds, fit by constrained EM, enforce candidate quota with top-k, and save one immutable CSV per preregistered setting.

## 5. Experiment

Compare V1 and one prespecified noise-corrected candidate on the same authorized accuracy leaderboard. Use at most two uploads, only if allowed; no row-level feedback inference. Success requires score >94% on that metric. Otherwise reject or revise only after the result.

## 6. Risks

Noise rates are not identifiable without assumptions/anchors; committee labels may encode genuine rules rather than errors.

## 7. Combines with

Compare strategies 26 and 27; keep a dated parameter registry.

## 8. Results log

Fixed-rate likelihood sensitivity was run for three preregistered cases; this is not the proposed EM procedure and estimates no flip rates. Committee diagnostics, candidate hashes and the identifiability limitation are in [`work/strat21/report.md`](work/strat21/report.md). No authorized upload or hidden-reference score exists; the official >94% criterion remains NOT RUN.
