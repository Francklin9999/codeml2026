"""Shared committee models and counterfactual scoring for local experiments."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import data


VARIANTS = {
    "V1": ("remote_flag", False, False, "logit"),
    "V2": ("five", False, False, "logit"),
    "V3": ("five", True, False, "logit"),
    "V4": ("remote_flag", False, False, "gbm"),
    "V5": ("remote_flag", False, True, "logit"),
}


def design(frame, region_mode, include_postal=False, interactions=False):
    matrix = data.features(frame, region_mode, include_postal)
    if interactions:
        matrix["remote_x_cote_r"] = matrix["remote"] * matrix["cote_r"]
        matrix["remote_x_heures"] = matrix["remote"] * matrix["heures"]
    return matrix


def fit_variant(history, variant="V1", seed=42, regularization=None):
    region_mode, postal, interactions, family = VARIANTS[variant]
    matrix = design(history, region_mode, postal, interactions)
    target = history[data.TARGET_COL].to_numpy()
    if family == "gbm":
        model = HistGradientBoostingClassifier(max_iter=150, max_leaf_nodes=15, random_state=seed)
        model.fit(matrix, target)
        return model, list(matrix.columns), {"family": family}
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    if regularization is None:
        search = GridSearchCV(
            pipeline, {"logisticregression__C": [0.1, 1.0, 10.0]}, scoring="roc_auc",
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=seed), n_jobs=1,
        )
        search.fit(matrix, target)
        model = search.best_estimator_
        details = {"family": family, "C": search.best_params_["logisticregression__C"],
                   "committee_cv_auc": float(search.best_score_)}
    else:
        model = pipeline.set_params(logisticregression__C=regularization).fit(matrix, target)
        details = {"family": family, "C": regularization}
    return model, list(matrix.columns), details


def variant_scores(model, columns, frame, history, variant="V1", neutral=True):
    region_mode, postal, interactions, family = VARIANTS[variant]
    matrix = design(frame, region_mode, postal, interactions).reindex(columns=columns, fill_value=0)
    if not neutral:
        return model.predict_proba(matrix)[:, 1]
    protected = data.region_columns(matrix) + data.postal_columns(matrix)
    protected += [column for column in matrix if column.startswith("remote_x_")]
    if family == "gbm":
        weight = float(data.remote_flag(history).mean())
        matrix["remote"] = 0.0
        central = model.predict_proba(matrix)[:, 1]
        matrix["remote"] = 1.0
        remote = model.predict_proba(matrix)[:, 1]
        return (1 - weight) * central + weight * remote
    if postal:
        central_history = history.loc[history.region_administrative.eq("Montreal")]
        if central_history.empty:
            raise ValueError("V3 needs Montreal rows to define a consistent postal reference")
        reference = data.features(central_history, "five", True)[protected].mean()
        matrix[protected] = reference.to_numpy()
    else:
        matrix[protected] = 0.0
    return model.predict_proba(matrix)[:, 1]


def baseline(history, candidates):
    categorical = ["programme_etudes", "region_administrative", "code_postal_3"]
    train = pd.get_dummies(history.drop(columns=[data.ID_COL, data.TARGET_COL, "groupe"], errors="ignore"),
                           columns=categorical)
    target = pd.get_dummies(candidates.drop(columns=[data.ID_COL, data.TARGET_COL, "groupe"], errors="ignore"),
                            columns=categorical).reindex(columns=train.columns, fill_value=0)
    model = RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42, n_jobs=1)
    model.fit(train, history[data.TARGET_COL])
    scores = model.predict_proba(target)[:, 1]
    return scores, float(model.predict(target).mean())


def quantile_map_distance(frame, history):
    mapped = frame.copy()
    central = np.sort(history.loc[history.region_administrative.isin(data.CENTRAL),
                                  "distance_domicile_campus_km"].to_numpy())
    for region in data.REGIONS:
        source = np.sort(history.loc[history.region_administrative.eq(region),
                                     "distance_domicile_campus_km"].to_numpy())
        mask = frame.region_administrative.eq(region)
        if not len(source) or not len(central):
            raise ValueError("distance mapping needs every region in the training data")
        values = frame.loc[mask, "distance_domicile_campus_km"].to_numpy()
        ranks = (np.searchsorted(source, values, side="left") +
                 np.searchsorted(source, values, side="right")) / (2 * len(source))
        mapped.loc[mask, "distance_domicile_campus_km"] = np.quantile(central, ranks)
    return mapped
