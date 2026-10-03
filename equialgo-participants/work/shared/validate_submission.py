"""Validate a local candidate submission against the supplied evaluation file."""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if __package__:
    from . import data
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from shared import data


def validate(path, candidates=None):
    candidates = data.load_candidates() if candidates is None else candidates
    submission = pd.read_csv(path, dtype={data.ID_COL: str})
    if list(submission.columns) != [data.ID_COL, data.TARGET_COL]:
        raise ValueError(f"header must be {data.SUBMISSION_HEADER}")
    if len(submission) != len(candidates):
        raise ValueError(f"expected {len(candidates)} rows, found {len(submission)}")
    if submission[data.ID_COL].duplicated().any():
        raise ValueError("candidate IDs must be unique")
    if submission[data.ID_COL].tolist() != candidates[data.ID_COL].astype(str).tolist():
        raise ValueError("candidate IDs and row order must match candidats_evaluation.csv")
    if not submission[data.TARGET_COL].isin([0, 1]).all():
        raise ValueError("decision_octroi must contain only 0 or 1, with no missing values")
    rate = float(submission[data.TARGET_COL].mean())
    if not data.RATE_MIN <= rate <= data.RATE_MAX:
        raise ValueError(f"grant rate {rate:.2%} is outside [36%, 44%]")
    return submission, {
        "rows": len(submission), "grants": int(submission[data.TARGET_COL].sum()),
        "rate": rate, "warning": not data.RATE_WARN_MIN <= rate <= data.RATE_WARN_MAX,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path)
    parser.add_argument("--data-root", type=Path,
                        help="explicit directory containing the supplied history and candidate CSV files")
    args = parser.parse_args()
    try:
        if args.data_root is not None:
            data.set_data_root(args.data_root)
        _, summary = validate(args.prediction)
    except (ValueError, OSError, pd.errors.ParserError) as error:
        parser.exit(1, f"INVALID: {error}\n")
    print(json.dumps(summary, indent=2))
    if summary["warning"]:
        print("WARNING: valid budget, but outside the 38–42% safety margin", file=sys.stderr)


if __name__ == "__main__":
    main()
