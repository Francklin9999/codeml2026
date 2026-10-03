"""Preregistered raw/log/spline income competition for candidate ranking."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

WORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK_DIR))

from shared import data, models
from shared.validate_submission import validate


SEED = 42
REGULARIZATION_C = 1.0
FORMS = ("raw", "log", "spline")


def design(frame: pd.DataFrame, form: str, transformer: np.ndarray | None = None):
    if form not in FORMS:
        raise ValueError(f"unknown income form: {form}")
    matrix = data.features(frame, "remote_flag", include_postal=False)
    matrix = matrix.drop(columns=["log_rev", "rev"])
    income = frame["revenu_familial_estime"].to_numpy(dtype=float) / 100000.0
    fitted_transformer = transformer
    if form == "raw":
        income_design = income[:, None]
        names = ["income_raw_per_100k"]
    elif form == "log":
        income_design = np.log(income)[:, None]
        names = ["income_log"]
    else:
        if fitted_transformer is None:
            fitted_transformer = np.quantile(income, [0.0, 1 / 3, 2 / 3, 1.0])
            if np.any(np.diff(fitted_transformer) <= 0):
                raise ValueError("restricted cubic spline needs four distinct training quantiles")
            income_design = restricted_cubic_basis(income, fitted_transformer)
        else:
            income_design = restricted_cubic_basis(income, fitted_transformer)
        names = [f"income_spline_{number}" for number in range(income_design.shape[1])]
    income_frame = pd.DataFrame(income_design, columns=names, index=frame.index)
    return pd.concat([matrix, income_frame], axis=1), fitted_transformer


def restricted_cubic_basis(income: np.ndarray, knots: np.ndarray) -> np.ndarray:
    values = np.asarray(income, dtype=float)
    knot_values = np.asarray(knots, dtype=float)
    if knot_values.shape != (4,) or np.any(np.diff(knot_values) <= 0):
        raise ValueError("restricted cubic spline requires four strictly increasing knots")
    right = knot_values[-1]
    penultimate = knot_values[-2]
    right_cube = np.maximum(values - right, 0.0) ** 3
    penultimate_tail = (np.maximum(values - penultimate, 0.0) ** 3 - right_cube) / (right - penultimate)
    nonlinear_terms = []
    for knot in knot_values[:-2]:
        first_tail = (np.maximum(values - knot, 0.0) ** 3 - right_cube) / (right - knot)
        nonlinear_terms.append(first_tail - penultimate_tail)
    return np.column_stack([values, *nonlinear_terms])


def fit_form(history: pd.DataFrame, form: str):
    matrix, transformer = design(history, form)
    estimator = make_pipeline(StandardScaler(),
                              LogisticRegression(C=REGULARIZATION_C, max_iter=2000,
                                                 random_state=SEED))
    estimator.fit(matrix, history[data.TARGET_COL].to_numpy(dtype=int))
    return estimator, list(matrix.columns), transformer


def predict(estimator, columns, transformer, frame: pd.DataFrame, form: str,
            neutralize_region: bool = False) -> np.ndarray:
    matrix, _ = design(frame, form, transformer)
    matrix = matrix.reindex(columns=columns, fill_value=0)
    if neutralize_region:
        matrix["remote"] = 0.0
    return estimator.predict_proba(matrix)[:, 1]


def evaluate_holdout(history: pd.DataFrame) -> pd.DataFrame:
    train, test = train_test_split(history, test_size=0.3, random_state=SEED,
                                   stratify=history[data.TARGET_COL])
    target = test[data.TARGET_COL].to_numpy(dtype=int)
    baseline, baseline_columns, _ = models.fit_variant(train, "V1", seed=SEED, regularization=1.0)
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
    for form in FORMS:
        estimator, columns, transformer = fit_form(train, form)
        raw = predict(estimator, columns, transformer, test, form)
        neutral = predict(estimator, columns, transformer, test, form, neutralize_region=True)
        top_k = data.top_k_mask(neutral, round(0.4 * len(test)), test.cote_r_equivalent)
        rows.append({"form": form, "holdout_rows": len(test),
                     "committee_accuracy_at_0_5": float(accuracy_score(target, raw >= 0.5)),
                     "committee_auc": float(roc_auc_score(target, raw)),
                     "top40_committee_agreement": float(accuracy_score(target, top_k)),
                     "top40_difference_vs_v1": int(np.count_nonzero(top_k != baseline_top_k))})
    return pd.DataFrame(rows)


def generate(history: pd.DataFrame, candidates: pd.DataFrame, output_dir: Path,
             v1_path: Path) -> list[dict]:
    summaries = []
    v1, _ = validate(v1_path, candidates)
    v1_prediction = v1[data.TARGET_COL].to_numpy(dtype=int)
    remote = data.remote_flag(candidates).astype(bool)
    for form in FORMS:
        estimator, columns, transformer = fit_form(history, form)
        neutral = predict(estimator, columns, transformer, candidates, form, neutralize_region=True)
        prediction = data.top_k_mask(neutral, data.BUDGET_K, candidates.cote_r_equivalent)
        path = output_dir / f"candidate_predictions_S30_income_{form}.csv"
        data.write_submission(prediction, path, candidates)
        summaries.append({"form": form, "path": str(path), "grants": int(prediction.sum()),
                          "candidate_count_remote": int(remote.sum()),
                          "candidate_count_central": int((~remote).sum()),
                          "remote_grants": int(prediction[remote].sum()),
                          "central_grants": int(prediction[~remote].sum()),
                          "candidate_differences_vs_v1": int(np.count_nonzero(
                              prediction != v1_prediction))})
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
