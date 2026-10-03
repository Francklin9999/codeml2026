"""Fit fixed-noise likelihood sensitivity models; no flip rates are estimated."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

WORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK_DIR))

from shared import data, models
from shared.validate_submission import validate


SEED = 42
REGULARIZATION_C = 1.0
SCENARIOS = ("pooled_05fn_02fp", "remote_10fn_02fp", "remote_05fn_06fp")


def rates_for_frame(frame: pd.DataFrame, scenario: str) -> tuple[np.ndarray, np.ndarray]:
    if scenario not in SCENARIOS:
        raise ValueError(f"scenario must be one of {SCENARIOS}")
    remote = data.remote_flag(frame).astype(bool)
    false_negative = np.full(len(frame), 0.05, dtype=float)
    false_positive = np.full(len(frame), 0.02, dtype=float)
    if scenario == "remote_10fn_02fp":
        false_negative[remote] = 0.10
    elif scenario == "remote_05fn_06fp":
        false_positive[remote] = 0.06
    return false_negative, false_positive


def observed_probability(latent_probability: np.ndarray, false_negative: np.ndarray,
                         false_positive: np.ndarray) -> np.ndarray:
    return false_positive + latent_probability * (1 - false_negative - false_positive)


def noise_objective(parameters: np.ndarray, scaled_features: np.ndarray, target: np.ndarray,
                    false_negative: np.ndarray, false_positive: np.ndarray,
                    regularization_c: float = REGULARIZATION_C):
    row_count = len(target)
    coefficients = parameters[:-1]
    intercept = parameters[-1]
    latent_score = scaled_features @ coefficients + intercept
    latent_probability = expit(latent_score)
    observed = observed_probability(latent_probability, false_negative, false_positive)
    clipped_observed = np.clip(observed, 1e-12, 1 - 1e-12)
    log_likelihood = target * np.log(clipped_observed) + (1 - target) * np.log1p(-clipped_observed)
    penalty_scale = 1.0 / (regularization_c * row_count)
    loss = -float(np.mean(log_likelihood)) + 0.5 * penalty_scale * float(coefficients @ coefficients)
    slope = 1 - false_negative - false_positive
    derivative_observed = slope * latent_probability * (1 - latent_probability)
    score_gradient = derivative_observed * (clipped_observed - target) / (
        clipped_observed * (1 - clipped_observed)) / row_count
    coefficient_gradient = scaled_features.T @ score_gradient + penalty_scale * coefficients
    gradient = np.append(coefficient_gradient, score_gradient.sum())
    return loss, gradient


def fit_noise_model(features: pd.DataFrame, target: np.ndarray, false_negative: np.ndarray,
                    false_positive: np.ndarray,
                    regularization_c: float = REGULARIZATION_C) -> dict:
    target = np.asarray(target)
    if target.ndim != 1 or len(target) == 0 or not np.isin(target, [0, 1]).all():
        raise ValueError("target must be a nonempty binary vector")
    if not np.isfinite(regularization_c) or regularization_c <= 0:
        raise ValueError("regularization_c must be positive and finite")
    target = target.astype(int)
    false_negative = np.asarray(false_negative, dtype=float)
    false_positive = np.asarray(false_positive, dtype=float)
    values = features.to_numpy(dtype=float)
    if values.ndim != 2 or len(values) != len(target) or not np.isfinite(values).all():
        raise ValueError("features must be a finite 2D matrix aligned with target")
    if false_negative.shape != target.shape or false_positive.shape != target.shape:
        raise ValueError("each target row needs one fixed false-negative and false-positive rate")
    if not np.isfinite(false_negative).all() or not np.isfinite(false_positive).all():
        raise ValueError("noise rates must be finite")
    if ((false_negative < 0.02) | (false_negative > 0.10) |
            (false_positive < 0.02) | (false_positive > 0.06)).any():
        raise ValueError("fixed rates are outside the preregistered sensitivity bounds")
    if ((false_negative + false_positive) >= 1).any():
        raise ValueError("combined flip rates must be less than one")
    scaler = StandardScaler().fit(values)
    scaled_features = scaler.transform(values)
    initial_parameters = np.zeros(scaled_features.shape[1] + 1)
    result = minimize(noise_objective, initial_parameters,
                      args=(scaled_features, target, false_negative, false_positive,
                            regularization_c), method="L-BFGS-B", jac=True,
                      options={"maxiter": 1000, "ftol": 1e-10})
    if not result.success or not np.isfinite(result.fun) or not np.isfinite(result.x).all():
        raise RuntimeError(f"fixed-noise optimization failed: {result.message}")
    return {"scaler": scaler, "coefficients": result.x[:-1], "intercept": float(result.x[-1]),
            "columns": list(features.columns), "iterations": int(result.nit),
            "objective": float(result.fun)}


def latent_probability(model: dict, features: pd.DataFrame,
                       neutralize_region: bool = False) -> np.ndarray:
    matrix = features.reindex(columns=model["columns"], fill_value=0.0).copy()
    if neutralize_region and "remote" in matrix:
        matrix["remote"] = 0.0
    scaled_features = model["scaler"].transform(matrix.to_numpy(dtype=float))
    latent_score = scaled_features @ model["coefficients"] + model["intercept"]
    return expit(latent_score)


def committee_probability(model: dict, features: pd.DataFrame,
                           false_negative: np.ndarray, false_positive: np.ndarray) -> np.ndarray:
    latent = latent_probability(model, features)
    return observed_probability(latent, false_negative, false_positive)


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
    rows = [{"scenario": "V1", "holdout_rows": len(test),
             "committee_accuracy_at_0_5": float(accuracy_score(target, baseline_raw >= 0.5)),
             "committee_auc": float(roc_auc_score(target, baseline_raw)),
             "top40_committee_agreement": float(accuracy_score(target, baseline_top_k))}]
    for scenario in SCENARIOS:
        false_negative, false_positive = rates_for_frame(train, scenario)
        fitted = fit_noise_model(train_features, train[data.TARGET_COL].to_numpy(),
                                 false_negative, false_positive)
        test_false_negative, test_false_positive = rates_for_frame(test, scenario)
        observed = committee_probability(fitted, test_features, test_false_negative,
                                         test_false_positive)
        latent = latent_probability(fitted, test_features, neutralize_region=True)
        top_k = data.top_k_mask(latent, round(0.4 * len(test)), test.cote_r_equivalent)
        rows.append({"scenario": scenario, "holdout_rows": len(test),
                     "committee_accuracy_at_0_5": float(accuracy_score(target, observed >= 0.5)),
                     "committee_auc": float(roc_auc_score(target, observed)),
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
    for scenario in SCENARIOS:
        false_negative, false_positive = rates_for_frame(history, scenario)
        fitted = fit_noise_model(data.features(history, "remote_flag", include_postal=False),
                                 history[data.TARGET_COL].to_numpy(),
                                 false_negative, false_positive)
        candidate_scores = latent_probability(fitted, candidate_features, neutralize_region=True)
        prediction = data.top_k_mask(candidate_scores, data.BUDGET_K,
                                     candidates.cote_r_equivalent)
        path = output_dir / f"candidate_predictions_S21_{scenario}.csv"
        data.write_submission(prediction, path, candidates)
        summaries.append({"scenario": scenario, "path": str(path), "grants": int(prediction.sum()),
                          "remote_count": int(remote.sum()), "central_count": int((~remote).sum()),
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
