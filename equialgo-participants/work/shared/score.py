"""Score local predictions against simulated references, never official labels."""
import argparse
from functools import lru_cache
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

if __package__:
    from . import data, models, reference_sim
    from .validate_submission import validate
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from shared import data, models, reference_sim
    from shared.validate_submission import validate


METRICS = {"accuracy": accuracy_score, "f1": f1_score, "balanced_accuracy": balanced_accuracy_score}


def binary(values, name):
    array = np.asarray(values)
    if array.ndim != 1 or not len(array) or not np.isin(array, [0, 1]).all():
        raise ValueError(f"{name} must be a nonempty binary vector")
    return array.astype(int)


def eo_gap(y_ref, y_pred, group):
    reference, prediction = binary(y_ref, "reference"), binary(y_pred, "prediction")
    group = np.asarray(group)
    if prediction.shape != reference.shape or group.shape != reference.shape:
        raise ValueError("reference, prediction and groups must have matching shapes")
    rates = []
    for name in np.unique(group):
        mask = (group == name) & (reference == 1)
        if not mask.any():
            raise ValueError(f"equal opportunity is undefined: no reference positives in group {name}")
        rates.append(float(prediction[mask].mean()))
    return max(rates) - min(rates)


@lru_cache(maxsize=512)
def random_agreement(reference, count, metric, n_random, seed):
    if n_random < 1:
        raise ValueError("n_random must be positive")
    rng = np.random.default_rng(seed)
    reference = np.asarray(reference)
    agreements = []
    for _ in range(n_random):
        draw = np.zeros(len(reference), dtype=int)
        draw[rng.choice(len(reference), count, replace=False)] = 1
        agreements.append(float(METRICS[metric](reference, draw)))
    return float(np.mean(agreements))


def official_like(y_pred, y_ref, group, baseline_pred, metric="accuracy", n_random=200,
                  rng=0, baseline_mode="measured"):
    prediction, reference = binary(y_pred, "prediction"), binary(y_ref, "reference")
    baseline_prediction = binary(baseline_pred, "baseline")
    group = np.asarray(group)
    if any(array.shape != reference.shape for array in [prediction, baseline_prediction, group]):
        raise ValueError("all inputs must have matching shapes")
    if metric not in METRICS or baseline_mode not in {"fixed", "measured"}:
        raise ValueError("unknown agreement metric or baseline mode")
    rate = float(prediction.mean())
    if not data.RATE_MIN <= rate <= data.RATE_MAX:
        return {"equity": 0.0, "utility": 0.0, "total": 0.0, "rate": rate, "budget_valid": False}
    measured_gap = eo_gap(reference, baseline_prediction, group)
    gap = eo_gap(reference, prediction, group)
    gap0 = data.BASELINE_EO_GAP if baseline_mode == "fixed" else measured_gap
    equity = 20 * float(np.clip((gap0 - gap) / gap0, 0, 1)) if gap0 > 0 else (20.0 if gap == 0 else 0.0)
    agreement = float(METRICS[metric](reference, prediction))
    random_value = random_agreement(tuple(reference.tolist()), int(prediction.sum()), metric, n_random, rng)
    utility = 15 * float(np.clip((agreement - random_value) / (1 - random_value), 0, 1)) if random_value < 1 else 15.0
    return {"equity": equity, "utility": utility, "total": equity + utility, "rate": rate,
            "budget_valid": True, "eo_gap": gap, "baseline_eo_gap": measured_gap,
            "equity_denominator": gap0, "agreement": agreement, "random_agreement": random_value}


def matrix(predictions, hypotheses, candidates, baseline_prediction, metrics, groupings, baseline_modes):
    rows = []
    for strategy, prediction in predictions.items():
        for hypothesis, labels in hypotheses.items():
            for metric in metrics:
                for grouping in groupings:
                    for mode in baseline_modes:
                        result = official_like(prediction, labels["candidates"], data.groups(candidates, grouping),
                                               baseline_prediction, metric, baseline_mode=mode)
                        rows.append({"strategy": strategy, "hypothesis": hypothesis, "metric": metric,
                                     "grouping": grouping, "baseline_mode": mode, **result})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pred", type=Path, required=True)
    parser.add_argument("--all-hypotheses", action="store_true")
    parser.add_argument("--hypothesis", default="H1")
    parser.add_argument("--metric", default="accuracy")
    parser.add_argument("--grouping", default="2")
    parser.add_argument("--baseline-mode", default="fixed,measured")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    submission, _ = validate(args.pred)
    history, candidates = data.load_both()
    hypotheses = reference_sim.references(history, candidates)
    if not args.all_hypotheses:
        hypotheses = {args.hypothesis: hypotheses[args.hypothesis]}
    baseline_scores, _ = models.baseline(history, candidates)
    baseline_prediction = data.top_k_mask(baseline_scores, data.BUDGET_K, candidates.cote_r_equivalent)
    result = matrix({args.pred.stem: submission[data.TARGET_COL].to_numpy()}, hypotheses, candidates,
                    baseline_prediction, args.metric.split(","),
                    [int(value) for value in args.grouping.split(",")], args.baseline_mode.split(","))
    print("SIMULATED ONLY: these are sensitivity estimates, not official scores.")
    print(result.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
