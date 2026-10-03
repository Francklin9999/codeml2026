"""Check a measured 72 mm print span; optionally save an adjusted board specification."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.geometry import SPEC_PATH, load_spec


def calibrated_spec(measured_span_mm, spec):
    if not np.isfinite(measured_span_mm) or measured_span_mm <= 0:
        raise ValueError("measured span must be positive and finite")
    factor = measured_span_mm / spec["print_check_span_mm"]
    if not 0.9 <= factor <= 1.1:
        raise ValueError("print scale differs by over 10%; check units and reprint")
    adjusted = dict(spec)
    adjusted["square_mm"] *= factor
    adjusted["marker_mm"] *= factor
    adjusted["window_mm"] = [value * factor for value in spec["window_mm"]]
    adjusted["print_check_span_mm"] = measured_span_mm
    adjusted["nominal_dimensions_verified_physically"] = True
    adjusted["measured_scale_factor"] = factor
    return adjusted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured-span-mm", type=float, required=True)
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--write-spec", type=Path)
    args = parser.parse_args()
    spec = load_spec(args.spec)
    try:
        adjusted = calibrated_spec(args.measured_span_mm, spec)
    except ValueError as error:
        parser.exit(1, f"Invalid span: {error}\n")
    passes = abs(args.measured_span_mm - spec["print_check_span_mm"]) <= spec["print_check_tolerance_mm"]
    print(json.dumps({"print_within_tolerance": passes, "scale_factor": adjusted["measured_scale_factor"]}, indent=2))
    if args.write_spec:
        args.write_spec.parent.mkdir(parents=True, exist_ok=True)
        args.write_spec.write_text(json.dumps(adjusted, indent=2), encoding="utf-8")
    elif not passes:
        parser.exit(1, "Reprint at 100%, or supply --write-spec to save the measured calibration.\n")
