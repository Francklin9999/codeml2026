"""Fit fixed-degree Student-t CDF links and emit neutralized rankings."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import t as student_t
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

WORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK_DIR))

from shared import data, models
from shared.validate_submission import validate


SEED = 42
REGULARIZATION_C = 1.0
DEGREES_OF_FREEDOM = (3, 10)


def link_objective(parameters: np.ndarray, scaled_features: np.ndarray, target: np.ndarray,
                   degrees_freedom: int, regularization_c: float = REGULARIZATION_C):
    row_count = len(target)
    coefficients = parameters[:-1]
    intercept = parameters[-1]
    latent_score = scaled_features @ coefficients + intercept
    probability = student_t.cdf(latent_score, degrees_freedom)
    clipped_probability = np.clip(probability, 1e-12, 1 - 1e-12)
    log_likelihood = target * np.log(clipped_probability) + (1 - target) * np.log1p(-clipped_probability)
    penalty_scale = 1.0 / (regularization_c * row_count)
    loss = -float(np.mean(log_likelihood)) + 0.5 * penalty_scale * float(coefficients @ coefficients)
    score_gradient = student_t.pdf(latent_score, degrees_freedom) * (
        clipped_probability - target) / (clipped_probability * (1 - clipped_probability))
    score_gradient = score_gradient / row_count
    coefficient_gradient = scaled_features.T @ score_gradient + penalty_scale * coefficients
    gradient = np.append(coefficient_gradient, score_gradient.sum())
    return loss, gradient


def fit_link(features: pd.DataFrame, target: np.ndarray, degrees_freedom: int,
             regularization_c: float = REGULARIZATION_C) -> dict:
    if degrees_freedom not in DEGREES_OF_FREEDOM:
        raise ValueError(f"degrees_freedom must be one of {DEGREES_OF_FREEDOM}")
    target = np.asarray(target)
    if target.ndim != 1 or len(target) == 0 or not np.isin(target, [0, 1]).all():
        raise ValueError("target must be a nonempty binary vector")
    if not np.isfinite(regularization_c) or regularization_c <= 0:
        raise ValueError("regularization_c must be positive and finite")
    target = target.astype(int)
    values = features.to_numpy(dtype=float)
    if values.ndim != 2 or len(values) != len(target) or not np.isfinite(values).all():
        raise ValueError("features must be a finite 2D matrix aligned with target")
    scaler = StandardScaler().fit(values)
    scaled_features = scaler.transform(values)
    initial_parameters = np.zeros(scaled_features.shape[1] + 1)
    result = minimize(link_objective, initial_parameters,
                      args=(scaled_features, target, degrees_freedom, regularization_c),
                      method="L-BFGS-B", jac=True,
                      options={"maxiter": 1000, "ftol": 1e-10})
    if not result.success or not np.isfinite(result.fun) or not np.isfinite(result.x).all():
        raise RuntimeError(f"Student-t link optimization failed for df={degrees_freedom}: {result.message}")
    return {"scaler": scaler, "coefficients": result.x[:-1], "intercept": float(result.x[-1]),
            "degrees_freedom": degrees_freedom, "columns": list(features.columns),
            "iterations": int(result.nit), "objective": float(result.fun)}


def predict_link(model: dict, features: pd.DataFrame, neutralize_region: bool = False) -> np.ndarray:
    matrix = features.reindex(columns=model["columns"], fill_value=0.0).copy()
    if neutralize_region and "remote" in matrix:
        matrix["remote"] = 0.0
    scaled_features = model["scaler"].transform(matrix.to_numpy(dtype=float))
    latent_score = scaled_features @ model["coefficients"] + model["intercept"]
    return student_t.cdf(latent_score, model["degrees_freedom"])


def evaluate_holdout(history: pd.DataFrame) -> pd.DataFrame:
    train, test = train_test_split(history, test_size=0.3, random_state=SEED,
                                   stratify=history[data.TARGET_COL])
    train_features = data.features(train, "remote_flag", include_postal=False)
    test_features = data.features(test, "remote_flag", include_postal=False,
                                   columns=list(train_features.columns))
    target = test[data.TARGET_COL].to_numpy(dtype=int)
    baseline, baseline_columns, _ = models.fit_variant(train, "V1", seed=SEED,
                                                        regularization=REGULARIZATION_C)
    baseline_raw = models.variant_scores(baseline, baseline_columns, test, train,
                                         "V1", neutral=False)
    baseline_neutral = models.variant_scores(baseline, baseline_columns, test, train,
                                             "V1", neutral=True)
    baseline_top_k = data.top_k_mask(baseline_neutral, round(0.4 * len(test)),
                                     test.cote_r_equivalent)
    rows = [{"form": "V1", "holdout_rows": len(test),
             "committee_accuracy_at_0_5": float(accuracy_score(target, baseline_raw >= 0.5)),
             "committee_auc": float(roc_auc_score(target, baseline_raw)),
             "top40_committee_agreement": float(accuracy_score(target, baseline_top_k))}]
    for degrees_freedom in DEGREES_OF_FREEDOM:
        fitted = fit_link(train_features, train[data.TARGET_COL].to_numpy(), degrees_freedom)
        raw_probability = predict_link(fitted, test_features)
        neutral_probability = predict_link(fitted, test_features, neutralize_region=True)
        top_k = data.top_k_mask(neutral_probability, round(0.4 * len(test)),
                                test.cote_r_equivalent)
        rows.append({"form": f"student_t_df{degrees_freedom}", "holdout_rows": len(test),
                     "committee_accuracy_at_0_5": float(accuracy_score(target,
                                                                         raw_probability >= 0.5)),
                     "committee_auc": float(roc_auc_score(target, raw_probability)),
                     "top40_committee_agreement": float(accuracy_score(target, top_k)),
                     "top40_difference_vs_v1": int(np.count_nonzero(top_k != baseline_top_k)),
                     "optimizer_iterations": fitted["iterations"]})
    return pd.DataFrame(rows)


def generate(history: pd.DataFrame, candidates: pd.DataFrame, output_dir: Path,
             v1_path: Path) -> list[dict]:
    candidate_features = data.features(candidates, "remote_flag", include_postal=False)
    v1, _ = validate(v1_path, candidates)
    v1_prediction = v1[data.TARGET_COL].to_numpy(dtype=int)
    remote = data.remote_flag(candidates).astype(bool)
    summaries = []
    for degrees_freedom in DEGREES_OF_FREEDOM:
        training_features = data.features(history, "remote_flag", include_postal=False)
        fitted = fit_link(training_features, history[data.TARGET_COL].to_numpy(), degrees_freedom)
        candidate_scores = predict_link(fitted, candidate_features, neutralize_region=True)
        prediction = data.top_k_mask(candidate_scores, data.BUDGET_K,
                                     candidates.cote_r_equivalent)
        path = output_dir / f"candidate_predictions_S28_student_t_df{degrees_freedom}.csv"
        data.write_submission(prediction, path, candidates)
        summaries.append({"degrees_freedom": degrees_freedom, "path": str(path),
                          "grants": int(prediction.sum()), "remote_count": int(remote.sum()),
                          "central_count": int((~remote).sum()),
                          "remote_grants": int(prediction[remote].sum()),
                          "central_grants": int(prediction[~remote].sum()),
                          "candidate_differences_vs_v1": int(np.count_nonzero(
                              prediction != v1_prediction)),
                          "optimizer_iterations": fitted["iterations"]})
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--v1-path", type=Path, required=True)
    args = parser.parse_args()
    data.set_data_root(args.data_root)
    history, candidates = data.load_both()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    diagnostics = evaluate_holdout(history)
    diagnostics.to_csv(args.output_dir / "committee_holdout_diagnostics.csv", index=False)
    summaries = generate(history, candidates, args.output_dir, args.v1_path)
    print(diagnostics.to_string(index=False))
    print(pd.DataFrame(summaries).to_string(index=False))


if __name__ == "__main__":
    main()
