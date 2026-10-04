# DayOne · Strategy 19: Privacy-preserving epidemiology dashboard (anonymised aggregates)

| | |
|---|---|
| **Status** | DONE (Claude Code, 2026-10-03) |
| **Priority** | P3 (bonus) |
| **Effort** | 3 h |
| **Depends on** | validated records (strategies 8–10) or the synthetic CSV for the demo |
| **Rubric lines** | bonus "Tableau de bord simple d'agrégats anonymisés (tension, température, VIH/syphilis/hépatite C) illustrant l'usage épidémiologique des données"; Linking & privacy (10) |
| **Differs from 1–10** | Strategy 10 protects identifiers at capture. This is the **downstream use** the brief motivates ("aucune donnée exploitable pour l'épidémiologie"): aggregate indicators with formal disclosure control (small-cell suppression, k-anonymity checks, optional differential privacy) |
| **Work folder** | `dayone-participants/work/strat19/` |

---

## 1. Context you need

- `data/maternal_registry_synthetic.csv`: 200 rows × 31 numeric columns (age, education, consanguinity, desired pregnancy, hypertension and diabetes history, gravidity, parity, abortions, living children, previous caesarean, BMI, mean systolic / diastolic BP, haemoglobin, fasting glucose, proteinuria, HIV / syphilis / hepatitis C results, gestational age at enrolment and at birth, gestational diabetes, preterm birth, delivery type, newborn sex, birth weight, head circumference, breastfeeding, referral). Blanks in 9 columns (e.g. glucose 35, haemoglobin 23).
- Out of scope: risk prediction, triage, clinical decision support. A dashboard of **descriptive aggregates** is in scope (bonus).

## 2. The idea

A small dashboard (Streamlit or a static HTML page) built only from a **de-identified analytics view**:
- indicators: coverage of HIV / syphilis / hepatitis C testing and positivity rates; BP distribution and share above thresholds; haemoglobin distribution (anaemia share); birth-weight distribution and low-birth-weight share; preterm share; caesarean share; breastfeeding initiation;
- breakdowns by period and by health-facility area (never by individual);
- **disclosure control:** suppress cells with fewer than k = 5 records; coarsen ages into bands; optionally add Laplace noise (ε-differential privacy) to counts for public views;
- **missingness made visible:** the share of NON_FOURNI / INCONNU per indicator, because unknown ≠ negative (ties back to the status model).

## 3. Why it could score

It illustrates why the digitisation matters (the brief's epidemiology motivation), it shows privacy engineering beyond masking, and it reuses the status model in a meaningful way (missing data is reported, not hidden).

## 4. Implementation plan

### 4.1 Files

```
work/strat19/
  analytics_view.py    # from validated records or the CSV → de-identified table (no codes, no dates finer than month)
  indicators.py        # indicator definitions with numerators / denominators / missing counts
  disclosure.py        # small-cell suppression, banding, optional Laplace noise
  dashboard.py         # Streamlit app (or build_static.py for HTML)
  INDICATORS.md        # definitions, thresholds used, data limitations
```

### 4.2 Details

- Indicators defined with explicit denominators (e.g. "tested for HIV among women with ≥ 1 visit"; positivity "among tested").
- For the CSV: treat blanks as "non renseigné" and show them.
- DP option: Laplace(1/ε) on counts with ε = 1 for the public view; show the effect on small counts; never apply noise to the internal (authorised) view.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | No row-level data | the dashboard's data payload contains only aggregates (inspect network / files) |
| T2 | Small cells | every displayed cell has n ≥ 5 or is suppressed (automated check) |
| T3 | Indicator correctness | hand-computed values on the CSV match the dashboard for 5 indicators |
| T4 | Missingness | each indicator shows its missing / unknown share |
| T5 | Scope | no risk scores, triage colours or individual predictions anywhere |

## 6. Risks

Drifting into clinical interpretation; keep labels descriptive and add the scope disclaimer.

## 7. Combines with

Strategy 8 (validated store), 10 (role `analyste`), 6 (status model).

## 8. Results log

| Date | Who | Indicators | Suppressed cells | Notes |
|---|---|---|---|---|
| 2026-10-03 | Claude Code | 9 (HIV, syphilis, hep C, BP >= 140/90, anaemia, LBW, preterm, caesarean, breastfeeding) + age bands | 3 (counts < 5) | static HTML; missing counts shown; optional Laplace noise; `pytest work/strat19` 3/3 |

**Implementation notes (2026-10-03).** Descriptive only, no prediction.
