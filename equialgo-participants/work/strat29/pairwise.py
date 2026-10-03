"""Within-region Bradley-Terry ranking diagnostic and candidate generator."""
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
PAIR_SEED = 2901
MAX_PAIRS_PER_REGION = 25000


def feature_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    matrix = data.features(frame, "none", include_postal=False)
    return matrix.drop(columns=["remote"], errors="ignore")


def pairwise_training_data(history: pd.DataFrame, max_pairs_per_region: int = MAX_PAIRS_PER_REGION,
                           seed: int = PAIR_SEED) -> tuple[pd.DataFrame, np.ndarray]:
    if max_pairs_per_region < 1:
        raise ValueError("max_pairs_per_region must be positive")
    matrix = feature_matrix(history).to_numpy(dtype=float)
    target = history[data.TARGET_COL].to_numpy(dtype=int)
    groups = data.group5(history)
    generator = np.random.default_rng(seed)
    differences = []
    for region in data.REGIONS:
        region_indices = np.flatnonzero(groups == region)
        positive_indices = region_indices[target[region_indices] == 1]
        negative_indices = region_indices[target[region_indices] == 0]
        pair_count = len(positive_indices) * len(negative_indices)
        if pair_count == 0:
            continue
        sample_count = min(pair_count, max_pairs_per_region)
        flat_pairs = generator.choice(pair_count, size=sample_count, replace=False)
        positive_rows = positive_indices[flat_pairs // len(negative_indices)]
        negative_rows = negative_indices[flat_pairs % len(negative_indices)]
        differences.append(matrix[positive_rows] - matrix[negative_rows])
    if not differences:
        raise ValueError("no within-region positive-negative pairs are available")
    positive_differences = np.vstack(differences)
    pair_features = np.vstack([positive_differences, -positive_differences])
    pair_target = np.concatenate([np.ones(len(positive_differences)),
                                  np.zeros(len(positive_differences))]).astype(int)
    columns = feature_matrix(history).columns
    return pd.DataFrame(pair_features, columns=columns), pair_target


def fit_pairwise(history: pd.DataFrame, max_pairs_per_region: int = MAX_PAIRS_PER_REGION,
                 seed: int = PAIR_SEED):
    pair_features, pair_target = pairwise_training_data(history, max_pairs_per_region, seed)
    estimator = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000,
                                                                    random_state=seed))
    estimator.fit(pair_features, pair_target)
    return estimator, list(pair_features.columns), len(pair_target) // 2


def scores(estimator, columns, frame: pd.DataFrame) -> np.ndarray:
    return estimator.decision_function(feature_matrix(frame).reindex(columns=columns, fill_value=0))


def evaluate_holdout(history: pd.DataFrame) -> dict[str, float]:
    train, test = train_test_split(history, test_size=0.3, random_state=SEED,
                                   stratify=history[data.TARGET_COL])
    estimator, columns, pair_count = fit_pairwise(train)
    test_scores = scores(estimator, columns, test)
    test_target = test[data.TARGET_COL].to_numpy(dtype=int)
    test_top_k = data.top_k_mask(test_scores, round(0.4 * len(test)), test.cote_r_equivalent)
    baseline, baseline_columns, _ = models.fit_variant(train, "V1", seed=SEED, regularization=1.0)
    baseline_raw = models.variant_scores(baseline, baseline_columns, test, train,
                                         "V1", neutral=False)
    baseline_neutral = models.variant_scores(baseline, baseline_columns, test, train,
                                             "V1", neutral=True)
    baseline_top_k = data.top_k_mask(baseline_neutral, round(0.4 * len(test)),
                                     test.cote_r_equivalent)
    return {
        "holdout_pair_count": pair_count,
        "holdout_rows": len(test),
        "pairwise_committee_auc": float(roc_auc_score(test_target, test_scores)),
        "pairwise_top40_committee_agreement": float(accuracy_score(test_target, test_top_k)),
        "v1_committee_accuracy_at_0_5": float(accuracy_score(test_target, baseline_raw >= 0.5)),
        "v1_committee_auc": float(roc_auc_score(test_target, baseline_raw)),
        "v1_top40_committee_agreement": float(accuracy_score(test_target, baseline_top_k)),
    }


def generate(history: pd.DataFrame, candidates: pd.DataFrame, output_path: Path,
            v1_path: Path) -> dict:
    estimator, columns, pair_count = fit_pairwise(history)
    candidate_scores = scores(estimator, columns, candidates)
    prediction = data.top_k_mask(candidate_scores, data.BUDGET_K, candidates.cote_r_equivalent)
    data.write_submission(prediction, output_path, candidates)
    v1, _ = validate(v1_path, candidates)
    v1_prediction = v1[data.TARGET_COL].to_numpy(dtype=int)
    remote = data.remote_flag(candidates).astype(bool)
    return {"candidate_pair_count": pair_count, "grants": int(prediction.sum()),
            "candidate_count_remote": int(remote.sum()),
            "candidate_count_central": int((~remote).sum()),
            "remote_grants": int(prediction[remote].sum()),
            "central_grants": int(prediction[~remote].sum()),
            "candidate_differences_vs_v1": int(np.count_nonzero(prediction != v1_prediction))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--v1-path", type=Path, required=True)
    args = parser.parse_args()
    data.set_data_root(args.data_root)
    history, candidates = data.load_both()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    holdout = evaluate_holdout(history)
    output_path = args.output_dir / "candidate_predictions_S29_pairwise.csv"
    candidate_summary = generate(history, candidates, output_path, args.v1_path)
    print(pd.Series({**holdout, **candidate_summary, "candidate_path": str(output_path)}).to_json(indent=2))


if __name__ == "__main__":
    main()
