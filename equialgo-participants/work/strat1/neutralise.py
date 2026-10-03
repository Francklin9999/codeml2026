"""Fit V1-V5 committee models, neutralise region, and write diagnostics."""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from shared import data, models, reference_sim, score
from shared.validate_submission import validate

DEFAULT_OUTPUT = HERE.parent / "_local" / "strat1"


def fit_predict(history, candidates, variant, seed):
    model, columns, details = models.fit_variant(history, variant, seed=seed)
    raw = models.variant_scores(model, columns, candidates, history, variant, neutral=False)
    adjusted = models.variant_scores(model, columns, candidates, history, variant, neutral=True)
    prediction = data.top_k_mask(adjusted, data.BUDGET_K, candidates.cote_r_equivalent)
    return model, columns, details, raw, adjusted, prediction


def conditional_table(candidates, predictions):
    remote = data.remote_flag(candidates).astype(int)
    decile = pd.qcut(candidates.cote_r_equivalent, 10, labels=False, duplicates="drop")
    frame = pd.DataFrame({"decile": decile, "remote": remote})
    tables = []
    for label, prediction in predictions.items():
        group_rates = frame.assign(grant=prediction).groupby(["decile", "remote"], observed=False).grant.mean().unstack()
        group_rates = group_rates.rename(columns={0: "central_rate", 1: "remote_rate"})
        group_rates["gap_remote_minus_central"] = group_rates.remote_rate - group_rates.central_rate
        group_rates.insert(0, "variant", label)
        tables.append(group_rates.reset_index())
    return pd.concat(tables, ignore_index=True)


def stability(history, candidates, variant, seed, c_value, reference_prediction):
    target = history[data.TARGET_COL].to_numpy()
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    grants = []
    for fold, (train_idx, _) in enumerate(folds.split(np.zeros(len(target)), target)):
        fold_history = history.iloc[train_idx]
        model, columns, _ = models.fit_variant(fold_history, variant, seed=seed + fold,
                                                regularization=c_value)
        adjusted = models.variant_scores(model, columns, candidates, fold_history, variant, neutral=True)
        grants.append(data.top_k_mask(adjusted, data.BUDGET_K, candidates.cote_r_equivalent))
    overlaps = []
    for left, right in combinations(grants, 2):
        union = np.logical_or(left, right).sum()
        overlaps.append(float(np.logical_and(left, right).sum() / union) if union else 1.0)
    return {"mean_pairwise_jaccard": float(np.mean(overlaps)),
            "min_pairwise_jaccard": float(np.min(overlaps)),
            "mean_vs_full_jaccard": float(np.mean([
                np.logical_and(item, reference_prediction).sum() / np.logical_or(item, reference_prediction).sum()
                for item in grants]))}


def committee_cv_auc(history, variant, c_value, seed):
    region_mode, postal, interactions, family = models.VARIANTS[variant]
    matrix = models.design(history, region_mode, postal, interactions)
    target = history[data.TARGET_COL].to_numpy()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    if family == "gbm":
        from sklearn.ensemble import HistGradientBoostingClassifier
        estimator = HistGradientBoostingClassifier(max_iter=150, max_leaf_nodes=15, random_state=seed)
    else:
        estimator = make_pipeline(StandardScaler(), LogisticRegression(C=c_value, max_iter=2000))
    return float(cross_val_score(estimator, matrix, target, cv=cv, scoring="roc_auc", n_jobs=1).mean())


def coefficient_table(model, columns, variant):
    if variant == "V4":
        return pd.DataFrame(columns=["variant", "feature", "coefficient"])
    coefs = model.named_steps["logisticregression"].coef_[0]
    return pd.DataFrame({"variant": variant, "feature": columns, "coefficient": coefs,
                         "abs_coefficient": np.abs(coefs)}).sort_values("abs_coefficient", ascending=False)


def markdown_table(frame):
    values = frame.fillna("").astype(str)
    headers = list(values.columns)
    rows = values.to_numpy().tolist()
    return "\n".join(["| " + " | ".join(headers) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(row) + " |" for row in rows])


def run(seed=42, output_dir=DEFAULT_OUTPUT):
    output_dir.mkdir(parents=True, exist_ok=True)
    history, candidates = data.load_both()
    predictions, fit_info, coefficients, raw_preds = {}, [], [], {}
    for variant in models.VARIANTS:
        model, columns, details, raw, adjusted, prediction = fit_predict(history, candidates, variant, seed)
        predictions[variant] = prediction
        raw_preds[variant] = data.top_k_mask(raw, data.BUDGET_K, candidates.cote_r_equivalent)
        path = output_dir / f"candidate_predictions_{variant}.csv"
        data.write_submission(prediction, path, candidates)
        c_value = details.get("C", 1.0)
        stability_result = stability(history, candidates, variant, seed, c_value, prediction)
        fit_info.append({"variant": variant, "family": details["family"], "C": details.get("C"),
                         "grid_cv_auc": details.get("committee_cv_auc"),
                         "committee_cv_auc_fixed_C": committee_cv_auc(history, variant, c_value, seed),
                         **stability_result})
        coefficients.append(coefficient_table(model, columns, variant))

    cond = conditional_table(candidates, {
        **{f"{variant}_committee": prediction for variant, prediction in raw_preds.items()}, **predictions,
    })
    cond.to_csv(output_dir / "conditional_parity.csv", index=False)
    coef = pd.concat(coefficients, ignore_index=True)
    coef.to_csv(output_dir / "coefficients.csv", index=False)
    pd.DataFrame(fit_info).to_csv(output_dir / "fit_stability.csv", index=False)

    references = reference_sim.references(history, candidates, seed)
    baseline_scores, _ = models.baseline(history, candidates)
    baseline_prediction = data.top_k_mask(baseline_scores, data.BUDGET_K, candidates.cote_r_equivalent)
    score_rows = []
    for variant, prediction in predictions.items():
        for hypothesis, labels in references.items():
            result = score.official_like(prediction, labels["candidates"], data.groups(candidates, 2),
                                         baseline_prediction, metric="accuracy", baseline_mode="fixed")
            score_rows.append({"variant": variant, "hypothesis": hypothesis, **result})
    simulated = pd.DataFrame(score_rows)
    simulated.to_csv(output_dir / "simulated_scores.csv", index=False)
    write_report(HERE / "report_01.md", fit_info, coef, cond, simulated)
    for variant in models.VARIANTS:
        _, summary = validate(output_dir / f"candidate_predictions_{variant}.csv")
        print(f"{variant}: {summary['grants']} grants ({summary['rate']:.1%}); candidate file valid")
    print(f"Wrote report and diagnostics under {output_dir}")


def write_report(path, fit_info, coefficients, conditional, simulated):
    lines = ["# Strategy 1: neutralisation results", "",
             "These are candidate outputs and sensitivity analyses only. Simulated scores compare predictions "
             "with hypotheses generated from the same supplied data and model families; they are not the hidden "
             "reference, independent ground truth, or official scores.", "",
             "## Committee fit and stability", "",
             "Five-fold AUC is on the committee label; selected-C AUC reuses the tuning folds and is optimistic, "
             "not an independent estimate. Logistic coefficients are standardized-pipeline coefficients. "
             "Stability uses five stratified 80/20 refits and pairwise Jaccard of each refit's top-1,600 candidate set. "
             "This is a lightweight proxy for the proposed 25 refits and does not establish sampling robustness.", "",
             markdown_table(pd.DataFrame(fit_info)), "",
             "## Largest absolute logistic coefficients", "",
             coefficients.sort_values("abs_coefficient", ascending=False).groupby("variant", sort=False).head(8)
             [["variant", "feature", "coefficient"]].pipe(markdown_table), "",
             "## Conditional parity", "",
             "Rates are by candidate academic decile, comparing remote and central candidates. Committee rows are "
             "unneutralized top-1,600 selections; variant rows are neutralized selections. Summary shows mean absolute "
             "remote-central gap and number of deciles exceeding 3 percentage points.", "",
             markdown_table(conditional.groupby("variant", as_index=False).agg(
                 mean_abs_gap=("gap_remote_minus_central", lambda values: values.abs().mean()),
                 deciles_over_3pp=("gap_remote_minus_central", lambda values: int((values.abs() > .03).sum())))
                 .round(3)), "",
             "## Simulated score sensitivity", "",
             "Fixed published baseline denominator (0.270), equal opportunity over Centre/Eloignee, accuracy agreement. "
             "All results are simulated only and inherit the assumptions and self-reference limitations above.", "",
             markdown_table(simulated.pivot(index="variant", columns="hypothesis", values="total").round(2)
                            .reset_index()), "",
             "Detailed tables and named candidate CSVs are in `work/_local/strat1/`. No candidate is designated as the "
             "official submission.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    run(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
