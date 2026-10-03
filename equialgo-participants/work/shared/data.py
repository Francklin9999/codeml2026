"""Shared data loaders, group helpers and feature construction (strat1.md §4.3).

Every EquiAlgo strategy should import this module instead of re-implementing
loading, group definitions or feature encoding, so that all strategies see the
same columns in the same order.

Typical use (from work/strat<N>/):

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # = work/
    from shared import data
    hist, cand = data.load_history(), data.load_candidates()
    X_hist, X_cand = data.build_xy("remote_flag", include_postal=False)
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- paths
SHARED_DIR = Path(__file__).resolve().parent
WORK_DIR = SHARED_DIR.parent
ROOT = WORK_DIR.parent                      # = equialgo-participants/
DATA_DIR = ROOT / "data"
HIST_CSV = DATA_DIR / "donnees_demandes.csv"
CAND_CSV = DATA_DIR / "candidats_evaluation.csv"


def set_data_root(data_root) -> None:
    """Use an explicit directory containing the two supplied IVADO CSV files."""
    global DATA_DIR, HIST_CSV, CAND_CSV
    root = Path(data_root).resolve()
    history_path = root / "donnees_demandes.csv"
    candidates_path = root / "candidats_evaluation.csv"
    missing = [str(path) for path in (history_path, candidates_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("data root is missing: " + ", ".join(missing))
    DATA_DIR, HIST_CSV, CAND_CSV = root, history_path, candidates_path
    _load_history.cache_clear()
    _load_candidates.cache_clear()
    _categories.cache_clear()

# --------------------------------------------------------------------------- constants
REMOTE = ["Bas-Saint-Laurent", "Cote-Nord", "Gaspesie-Iles-de-la-Madeleine"]
CENTRAL = ["Montreal", "Capitale-Nationale"]
REGIONS = ["Montreal", "Capitale-Nationale", "Bas-Saint-Laurent", "Cote-Nord",
           "Gaspesie-Iles-de-la-Madeleine"]
GROUPS2 = ["Centre", "Eloignee"]            # names used by the notebook (groupe_region)
N_HIST, N_CAND = 10_000, 4_000
BUDGET_K = 1_600                            # 40% of 4,000
RATE_MIN, RATE_MAX = 0.36, 0.44             # official hard window
RATE_WARN_MIN, RATE_WARN_MAX = 0.38, 0.42   # our safety margin
BASELINE_EO_GAP = 0.270                     # published official baseline gap
ID_COL, TARGET_COL = "id_candidat", "decision_octroi"
SUBMISSION_HEADER = f"{ID_COL},{TARGET_COL}"


# --------------------------------------------------------------------------- loaders
@lru_cache(maxsize=1)
def _load_history() -> pd.DataFrame:
    return pd.read_csv(HIST_CSV)


@lru_cache(maxsize=1)
def _load_candidates() -> pd.DataFrame:
    return pd.read_csv(CAND_CSV)


def load_history() -> pd.DataFrame:
    """10,000 historical applications (with the biased `decision_octroi`). Fresh copy."""
    return _load_history().copy()


def load_candidates() -> pd.DataFrame:
    """4,000 candidates to score (no label). Fresh copy. Row order = submission order."""
    return _load_candidates().copy()


def load_both() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_history(), load_candidates()


# --------------------------------------------------------------------------- groups
def remote_flag(df: pd.DataFrame) -> np.ndarray:
    """1.0 for Bas-Saint-Laurent / Cote-Nord / Gaspesie, else 0.0."""
    return df["region_administrative"].isin(REMOTE).to_numpy().astype(float)


def group2(df: pd.DataFrame) -> np.ndarray:
    """'Centre' / 'Eloignee' (same labels as the notebook's `groupe_region`)."""
    return np.where(df["region_administrative"].isin(REMOTE), "Eloignee", "Centre")


def group5(df: pd.DataFrame) -> np.ndarray:
    """The five administrative regions (string array)."""
    return df["region_administrative"].to_numpy().astype(str)


def groups(df: pd.DataFrame, grouping: int | str = 2) -> np.ndarray:
    """grouping in {2, 5}: 2 groups Centre/Eloignee, or the 5 regions."""
    g = int(grouping)
    if g == 2:
        return group2(df)
    if g == 5:
        return group5(df)
    raise ValueError(f"grouping must be 2 or 5, got {grouping!r}")


# --------------------------------------------------------------------------- features
@lru_cache(maxsize=1)
def _categories() -> dict[str, list[str]]:
    """Category universes taken from the union of both files, so that dummies are
    identical whatever subset of rows `features()` receives."""
    h, c = _load_history(), _load_candidates()
    both = pd.concat([h, c], ignore_index=True)
    return {
        "programme_etudes": sorted(both["programme_etudes"].unique()),
        "code_postal_3": sorted(both["code_postal_3"].unique()),
    }


def features(df: pd.DataFrame, region_mode: str = "remote_flag", include_postal: bool = False,
             columns: list[str] | None = None) -> pd.DataFrame:
    """Numeric design matrix as in strat1.md §4.3.

    region_mode:
      "remote_flag" -> one column `remote` (1 for the 3 remote regions)
      "five"        -> 4 dummies `reg_*`, Montreal as reference
      "none"        -> no region information at all
    include_postal: add the 17 `cp_*` dummies (first postal code is the reference).
    columns: if given, the result is aligned with `reindex(columns=columns, fill_value=0)`
             (use the training matrix's columns when scoring candidates).
    Column order is deterministic: numeric block, programme dummies, region block, postal block.
    """
    cats = _categories()
    X = pd.DataFrame(index=df.index)
    X["cote_r"] = df["cote_r_equivalent"].astype(float)
    X["log_rev"] = np.log(df["revenu_familial_estime"].astype(float))
    X["rev"] = df["revenu_familial_estime"].astype(float) / 1e5
    X["heures"] = df["heures_travail_semaine"].astype(float)
    X["log_dist"] = np.log1p(df["distance_domicile_campus_km"].astype(float))
    X["dist"] = df["distance_domicile_campus_km"].astype(float) / 100
    X["premgen"] = df["premiere_generation_universitaire"].astype(float)
    prog = pd.Categorical(df["programme_etudes"], categories=cats["programme_etudes"])
    X = X.join(pd.get_dummies(prog, prefix="prog", drop_first=True).astype(float).set_axis(df.index))
    if region_mode == "remote_flag":
        X["remote"] = remote_flag(df)
    elif region_mode == "five":
        reg = pd.Categorical(df["region_administrative"], categories=REGIONS)
        d = pd.get_dummies(reg, prefix="reg").astype(float).set_axis(df.index)
        X = X.join(d.drop(columns="reg_Montreal"))
    elif region_mode != "none":
        raise ValueError("region_mode must be 'remote_flag', 'five' or 'none'")
    if include_postal:
        cp = pd.Categorical(df["code_postal_3"], categories=cats["code_postal_3"])
        X = X.join(pd.get_dummies(cp, prefix="cp", drop_first=True).astype(float).set_axis(df.index))
    X.columns = [str(c) for c in X.columns]
    if columns is not None:
        X = align(X, columns)
    return X


def align(X: pd.DataFrame, columns) -> pd.DataFrame:
    """Align a matrix with the training columns (the notebook's warning, §4.3)."""
    return X.reindex(columns=list(columns), fill_value=0.0)


def build_xy(region_mode: str = "remote_flag", include_postal: bool = False
             ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(X_hist, X_cand) with identical, aligned columns."""
    h, c = load_history(), load_candidates()
    Xh = features(h, region_mode, include_postal)
    Xc = features(c, region_mode, include_postal, columns=list(Xh.columns))
    return Xh, Xc


def region_columns(X: pd.DataFrame) -> list[str]:
    """Columns of X that carry the region (remote, reg_*)."""
    return [c for c in X.columns if c == "remote" or c.startswith("reg_")]


def postal_columns(X: pd.DataFrame) -> list[str]:
    return [c for c in X.columns if c.startswith("cp_")]


# --------------------------------------------------------------------------- helpers
def top_k_mask(score, k: int = BUDGET_K, tiebreak=None) -> np.ndarray:
    """0/1 int array granting exactly the k highest scores.

    Ties are broken by `tiebreak` (higher wins; default: cote R is NOT assumed, so pass it),
    then by row order, deterministically.
    """
    score = np.asarray(score, dtype=float)
    if score.ndim != 1 or not np.isfinite(score).all():
        raise ValueError("scores must be a finite one-dimensional array")
    n = len(score)
    tb = np.zeros(n) if tiebreak is None else np.asarray(tiebreak, dtype=float)
    if not isinstance(k, (int, np.integer)) or not 0 <= k <= n:
        raise ValueError(f"k must be an integer between 0 and {n}")
    if tb.shape != score.shape or not np.isfinite(tb).all():
        raise ValueError("tiebreak must contain one finite value per score")
    order = np.lexsort((np.arange(n), -tb, -score))
    out = np.zeros(n, dtype=int)
    out[order[:k]] = 1
    return out


def submission_frame(pred, cand: pd.DataFrame | None = None) -> pd.DataFrame:
    """DataFrame in the official format: id_candidat, decision_octroi."""
    cand = load_candidates() if cand is None else cand
    pred = np.asarray(pred)
    if pred.ndim != 1 or not np.isin(pred, [0, 1]).all():
        raise ValueError("predictions must be a one-dimensional binary array")
    pred = pred.astype(int)
    if len(pred) != len(cand):
        raise ValueError(f"{len(pred)} predictions for {len(cand)} candidates")
    return pd.DataFrame({ID_COL: cand[ID_COL].to_numpy(), TARGET_COL: pred})


def write_submission(pred, path, cand: pd.DataFrame | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    submission_frame(pred, cand).to_csv(path, index=False)
    return path


if __name__ == "__main__":
    h, c = load_both()
    print(f"history {h.shape}, candidates {c.shape}, grant rate {h[TARGET_COL].mean():.4f}")
    print(pd.Series(group2(c)).value_counts().to_dict(), pd.Series(group5(c)).value_counts().to_dict())
    Xh, Xc = build_xy("remote_flag", False)
    print("features remote_flag:", list(Xh.columns))
    print("features five+postal:", features(h.head(3), "five", True).shape[1], "columns")
