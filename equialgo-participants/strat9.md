# EquiAlgo · Strategy 9: Path-specific counterfactual fairness (which proxies to neutralise)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (principled variant of strategy 1) |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (committee model), 5 (proxy table) |
| **Rubric lines** | Technical (35), Governance (25: a defensible, explicit choice) |
| **Work folder** | `equialgo-participants/work/strat9/` |

---

## 1. Context you need

Strategy 1 removes only the **direct** region → decision effect. But region also shapes distance, postal code, hours worked, income and first-generation status. The committee gives **positive** weight to hours (+0.76 std.) and log income (+0.74), and remote applicants work more (≈ 13 vs 9 h/week). So whether those indirect paths count as bias changes who should be granted. The reference's view is unknown.

## 2. The idea

Draw the causal graph, decide **path by path** which influences of region are legitimate, and compute counterfactual predictions that remove only the illegitimate paths (Kusner et al. 2017, *Counterfactual Fairness*; Chiappa 2019, *Path-Specific Counterfactual Fairness*). Test several path sets in the simulator.

## 3. Why it could score

If the reference also neutralises geography-driven differences, this matches it better than strategy 1. Either way, an explicit DAG with a justified legitimate-path set is a strong governance argument.

## 4. Implementation plan

### 4.1 Files

```
work/strat9/
  causal_dag.png            # drawn with graphviz or networkx
  dag_justification.md      # one line per edge
  path_specific.py
  paths_vs_hypotheses.csv
  examples.md               # 5 candidates: original vs counterfactual features and decision
```

### 4.2 DAG (to justify edge by edge)

`region → {postal code, distance, hours, income, first-gen}`; `merit → cote R`; `{cote R, programme, hours, income, first-gen, distance, region} → committee decision`.

### 4.3 Abduction and counterfactual features

For each proxy `X`, estimate its region-dependent distribution and the individual's position within it:

```python
# within-region quantile mapping (robust for skewed variables like distance and income)
def counterfactual(x, region_i, target="central"):
    q = ecdf[region_i][X](x)                 # individual's quantile in own region
    return quantile[target][X](q)            # same quantile in the target region distribution
```

For the target, use the pooled central distribution (Montréal + Capitale-Nationale) or the population average over regions. Postal code has no within-region variation in meaning: drop it.

### 4.4 Path sets to evaluate

| Set | Neutralised paths | Interpretation |
|---|---|---|
| P0 | direct only | = strategy 1 |
| P1 | direct + postal + distance | pure geography removed |
| P2 | P1 + hours + income | all socio-economic channels removed |
| P3 | everything except cote R and programme | ≈ merit only |

Score counterfactual features with the committee model **without** the region term (or with region neutralised), grant the top 1,600.

### 4.5 Direction check

Report, for each path set, the group grant rates on candidates. Expect P2 to *lower* remote rates relative to P1 (because the committee rewards hours, which are higher in remote regions). Make sure the team understands and can explain that before choosing.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | P0 equals strategy 1 V1 | identical predictions |
| T2 | Counterfactual sanity | after mapping, distance distributions of remote and central candidates match (KS test p > 0.05) |
| T3 | Simulator | P0–P3 scored under H1–H6; expected: P0 best under H1, P1 under H4, P3 near-best under H2 |
| T4 | Choice | with strategy 3's weights, a recommended path set and the points gained vs P0 |
| T5 | Explainability | `examples.md` with 5 concrete candidates the jury can follow |

**Kill:** if P1–P3 never beat P0 under any plausible hypothesis, keep P0 and use this work only for the governance section.

## 6. Risks

Counterfactual features for an individual are model-dependent assumptions. Present them as a policy choice, not a fact about the person.

## 7. Combines with

Strategy 1 (P0), 5 (legitimacy column), 8 (P-variants as components), 10 (governance argument).

## 8. Results log

| Date | Who | Path set | Group rates (C / R) | Sim. weighted total /35 | Verdict |
|---|---|---|---|---|---|
| | | | | | |
