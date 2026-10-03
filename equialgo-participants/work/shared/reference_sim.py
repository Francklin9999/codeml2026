"""Hypothetical references; none is the organisers' hidden reference."""
import numpy as np

from . import data, models


def balanced_noise(labels, fraction, seed):
    rng = np.random.default_rng(seed)
    result = np.asarray(labels, dtype=int).copy()
    count = round(len(result) * fraction / 2)
    positive = rng.choice(np.flatnonzero(result == 1), count, replace=False)
    negative = rng.choice(np.flatnonzero(result == 0), count, replace=False)
    result[positive], result[negative] = 0, 1
    return result


def references(history=None, candidates=None, seed=42):
    history = data.load_history() if history is None else history
    candidates = data.load_candidates() if candidates is None else candidates
    model, columns, _ = models.fit_variant(history, "V1", seed)
    nonlinear, nonlinear_columns, _ = models.fit_variant(history, "V4", seed)
    train_need = np.column_stack([
        history.cote_r_equivalent, -np.log(history.revenu_familial_estime),
        history.heures_travail_semaine, history.premiere_generation_universitaire,
    ])
    mean, std = train_need.mean(axis=0), train_need.std(axis=0)
    std[std == 0] = 1
    outputs = {name: {} for name in ["H1", "H1n5", "H1n10", "H2", "H3w0.25", "H3w0.5", "H3w1", "H4", "H5"]}
    for split, frame in [("history", history), ("candidates", candidates)]:
        count = round(len(frame) * 0.4)
        tie = frame.cote_r_equivalent.to_numpy()
        neutral = models.variant_scores(model, columns, frame, history, "V1")
        outputs["H1"][split] = data.top_k_mask(neutral, count, tie)
        for name, noise in [("H1n5", 0.05), ("H1n10", 0.1)]:
            outputs[name][split] = balanced_noise(outputs["H1"][split], noise, seed)
        outputs["H2"][split] = data.top_k_mask(tie, count)
        need = np.column_stack([frame.cote_r_equivalent, -np.log(frame.revenu_familial_estime),
                                frame.heures_travail_semaine, frame.premiere_generation_universitaire])
        standardized = (need - mean) / std
        for weight in [0.25, 0.5, 1]:
            scores = standardized[:, 0] + weight * standardized[:, 1:].sum(axis=1)
            outputs[f"H3w{weight}"][split] = data.top_k_mask(scores, count, tie)
        mapped = models.quantile_map_distance(frame, history)
        scores = models.variant_scores(model, columns, mapped, history, "V1")
        outputs["H4"][split] = data.top_k_mask(scores, count, tie)
        scores = models.variant_scores(nonlinear, nonlinear_columns, frame, history, "V4")
        outputs["H5"][split] = data.top_k_mask(scores, count, tie)
    return outputs
