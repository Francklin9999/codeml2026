# EquiAlgo · Strategy 13: Adversarial debiasing (in-processing with an adversary that tries to recover region)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (interesting contrast; less likely to win than strategy 1) |
| **Effort** | 3–4 h |
| **Depends on** | strategy 2 (simulator) |
| **Rubric lines** | Technical (35), Pareto front (adversary weight as the knob), Pitch (method comparison) |
| **Differs from 1–10** | Strategy 6 uses fairlearn's reductions / post-processing; strategy 1 neutralises a known coefficient. This trains a neural scorer **jointly with an adversary** so the score carries no information about region given the label (equal-opportunity flavour), in the spirit of Zhang, Lemoine & Mitchell (2018) |
| **Work folder** | `equialgo-participants/work/strat13/` |

---

## 1. Context you need

See strategy 1 §1 for data, scoring and groups. Torch is available in the global Python on this machine (`torch 2.4.1+cu121`); the challenge venv needs it added if used there.

## 2. The idea

Predictor `f(x)` (small MLP on all non-region features) outputs a score; adversary `a(f(x), y)` tries to predict `remote` from the score **and the label** (conditioning on the label targets equal opportunity / equalised odds rather than parity). Train with the gradient-reversal objective:

`min_f max_a  L_pred(f) − λ · L_adv(a)`

Sweep λ to trace a Pareto front. Rank candidates by `f(x)`, grant top 1,600.

Important twist: the labels are the **biased committee decisions**, so the adversary equalises opportunity relative to biased labels (same limitation as strategy 6). Variant B fixes this by training on strategy 11's repaired labels.

## 3. Why it could score

It offers a different trade-off curve and a strong "we tried the state of the art and here is why it's not enough on its own" story; variant B may be competitive.

## 4. Implementation plan

### 4.1 Files

```
work/strat13/
  adversarial.py      # model, training loop, gradient reversal
  sweep_lambda.py
  report_13.md
```

### 4.2 Architecture and training

```python
class Scorer(nn.Module):   # input: standardised features without region / postal code
    def __init__(s, d): super().__init__(); s.net = nn.Sequential(nn.Linear(d, 32), nn.ReLU(), nn.Linear(32, 1))
class Adversary(nn.Module):  # input: [logit, y]
    def __init__(s): super().__init__(); s.net = nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 1))
# loop: for each batch
#   z = scorer(x); loss_pred = bce(z, y)
#   r_hat = adversary(torch.cat([z.detach(), y], 1)); loss_adv = bce(r_hat, remote)   → update adversary
#   r_hat2 = adversary(torch.cat([z, y], 1)); loss = loss_pred - lam * bce(r_hat2, remote) → update scorer
```

Standard tricks: pre-train the scorer a few epochs, then alternate; Adam lr 1e-3; 50–100 epochs; early stopping on a validation split; 5 seeds per λ (adversarial training is noisy).

### 4.3 Sweep

λ ∈ {0, 0.1, 0.3, 1, 3, 10}; variants A (committee labels) and B (strategy 11 repaired labels).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Adversary effectiveness | adversary AUC for region given (score, label) falls toward 0.5 as λ grows |
| T2 | Stability | across 5 seeds, the granted sets overlap ≥ 90% (Jaccard) at the chosen λ |
| T3 | Simulator | equity / utility under H1–H6 for each λ and variant |
| T4 | Comparison | vs strategies 1 and 6 on the same chart |

**Kill:** if T2 fails at every λ (too unstable) or it never beats strategy 6 in the simulator, keep only as a comparison point in the pitch.

## 6. Risks

Training instability; time cost. Cap at the effort estimate.

## 7. Combines with

Strategy 11 (repaired labels for variant B), 6 / 7 (Pareto comparison), 10 (pitch).

## 8. Results log

| Date | Who | Variant / λ | Adv. AUC | Seed stability | Sim. total /35 | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
