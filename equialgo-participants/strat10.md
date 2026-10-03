# EquiAlgo · Strategy 10: Governance, monitoring plan, model card and pitch

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (40 jury points) |
| **Effort** | 4–5 h |
| **Depends on** | strategy 4, 5 (diagnosis), the chosen mitigation (1 / 7 / 8 / 9) |
| **Rubric lines** | Governance & ethics (25), Pitch & code quality (15) |
| **Work folder** | `equialgo-participants/work/strat10/` |

---

## 1. Context you need

- Deliverables (GitHub repo): `predictions.csv` at the root, `audit_rapport.ipynb` (bias measurement, fairness metrics with justification, proxies), `model_corrige.py|.ipynb` (mitigation + Pareto front), `presentation.pdf` (5-minute pitch).
- The brief: *"Demographic parity and equal opportunity cannot both hold when the two groups have different profiles. Choose one and be ready to defend the choice."*
- The task includes *"propose a monitoring plan for production"*.

## 2. The idea

Treat governance and pitch as a deliverable with its own checklist: a defended metric choice, a model card, a monitoring plan with thresholds and owners, a human-review design, the legal context, reproducible code, and a 5-minute pitch built on three charts.

## 3. Why it could score

40 points are jury-judged here and teams tend to look alike. Concrete thresholds, owners and a simulated drift alert are what separates a plan from a paragraph.

## 4. Implementation plan

### 4.1 Files

```
work/strat10/
  governance.md          # becomes a section of audit_rapport.ipynb
  model_card.md
  monitoring_plan.md
  drift_demo.py          # simulated drift → alert
  pitch_outline.md       # → presentation.pdf
  qa_prep.md             # hardest questions and answers
run_all.py               # at the submission repo root: regenerates everything
```

### 4.2 Metric choice (write it out)

- **Equal opportunity:** among deserving applicants, the same chance in every region. Matches the grader and the mission.
- **Not demographic parity:** groups differ slightly in cote R (27.3 vs 28.0); parity would override real merit differences.
- **Honest cost:** EO needs a notion of "deserving" we cannot observe; in production it must be estimated on an independently reviewed sample (below).

### 4.3 Model card (Mitchell et al. 2019 sections)

Intended use; out-of-scope uses; training data (synthetic, 10k, committee labels known to be biased); features used, neutralised, dropped (from strategy 5); metrics by group (rates, conditional parity, simulated EO under hypotheses); Pareto front; limits (unknown reference, binary grouping, intersectionality with first-gen and income); ethical considerations.

### 4.4 Monitoring plan (table in `monitoring_plan.md`)

| Metric | Frequency | Threshold / alert | Owner | Action |
|---|---|---|---|---|
| Grant rate per region and per 2-group block | each cycle (monthly during intake) | gap > 5 pts **after conditioning on cote R deciles** | fairness officer | investigation + hold automated decisions for affected group |
| Score distribution drift | each cycle | PSI > 0.2 vs training (baseline from strategy 5) | data scientist | retrain review |
| Proxy drift (distance, hours, income by region) | each cycle | PSI > 0.2 | data scientist | re-check neutralisation |
| EO estimate on an audited sample | each cycle | TPR gap > 0.05 on ~200 files reviewed blind to region | independent review panel | recalibrate α / thresholds |
| Appeals rate and outcomes by region | monthly | appeal success rate differs > 10 pts | ombudsperson | case review |
| Budget adherence | each run | grant rate outside 38–42% | product owner | stop and recalibrate |
| Overrides in the human-review band | monthly | override rate > 20% or skewed by region | committee chair | audit |

### 4.5 Human in the loop

Review band around the cut (e.g. ranks 1,500–1,700): files reviewed by a panel blind to region and postal code; every override logged with a reason; quarterly audit of overrides by region.

### 4.6 Legal and policy context (verify wording before quoting)

- Québec's private-sector privacy act, as amended by Law 25 (section 12.1): when a decision is based exclusively on automated processing, the person must be informed and, on request, told the personal information used and the main factors, and be able to submit observations to someone who can review the decision. Design: notification text + explanation template + review route.
- Québec Charter of human rights and freedoms: region is not a listed ground, but it acts here as a proxy for socio-economic conditions; explain why we still treat the gap as unfair.

### 4.7 Pitch (5 min, `presentation.pdf`, ≤ 6 slides)

1. The gap, and how much is unexplained (strategy 4 headline + conditional curves).
2. Why deleting the column fails (strategy 5 chart).
3. Our fix in one sentence + Pareto front (strategy 1 / 7, fairlearn overlay from 6).
4. Results: group rates before / after, simulated robustness (strategy 2 / 3 / 8).
5. Governance: monitoring table, human review, Law 25 route.
6. Limits and what we would need from the institution.

### 4.8 Code quality

`run_all.py` regenerates `predictions.csv`, both notebooks (via `nbconvert --execute`) and all figures from a fresh clone; pinned `requirements.txt` (exact versions from `pip freeze`); README with the run order and the AI tools used.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Rubric checklist | every item in 4.2–4.7 present and linked to evidence in the notebooks |
| T2 | Drift dry run | `drift_demo.py` shifts distance/hours for remote candidates in a copy of the candidate file; the expected alerts fire, the others don't |
| T3 | Pitch timing | two timed rehearsals ≤ 5:00 |
| T4 | Hard questions | written answers to: "how do you know what *deserving* means?", "isn't using region at training time discriminatory?", "what if the reference counts income as bias?", "why this α?" |
| T5 | Reproducibility | fresh clone → venv → `python run_all.py` → identical `predictions.csv` (hash match) |

## 6. Risks

Legal statements stated wrongly. Quote only what was verified, with the source.

## 7. Combines with

Every other strategy; this is the narrative layer.

## 8. Results log

| Date | Who | Checklist | Pitch time | Repro hash match | Notes |
|---|---|---|---|---|---|
| | | | | | |
