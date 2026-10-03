"""Evaluate the local pipeline on generated images, including expected rejections."""
import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np

WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK))
from shared.geometry import LOCAL, board_size, load_spec
from strat1.synthetic import suite
from strat2.measure import measure


def evaluate(dataset, output, maximum_mae=0.5):
    cases = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for truth in cases:
        expected = truth["lens_present"] and truth["markers_present"]
        row = {"case": truth["case"], "expected_measurement": expected,
               "edge_height_mm": truth["edge_height_mm"]}
        try:
            result = measure(dataset / truth["image"], output / truth["case"])
            row.update({"measured": True, "A_error_mm": result["A_mm"] - truth["A_mm"],
                        "B_error_mm": result["B_mm"] - truth["B_mm"],
                        "perimeter_error_mm": result["perimeter_mm"] - truth["perimeter_mm"],
                        "reprojection_mm": result["calibration"]["reprojection_mm"], "reason": ""})
            if truth["edge_height_mm"]:
                corrected = measure(dataset / truth["image"], output / (truth["case"] + "_corrected"),
                                    camera_distance_mm=truth["camera_distance_mm"],
                                    edge_height_mm=truth["edge_height_mm"], nadir_mm=board_size(load_spec()) / 2)
                row["corrected_A_error_mm"] = corrected["A_mm"] - truth["A_mm"]
                row["corrected_B_error_mm"] = corrected["B_mm"] - truth["B_mm"]
        except (ValueError, OSError, cv2.error) as error:
            row.update({"measured": False, "reason": str(error)})
        rows.append(row)
    output.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    valid = [row for row in rows if row["expected_measurement"] and row["measured"] and row["edge_height_mm"] == 0]
    errors = [abs(row[key]) for row in valid for key in ["A_error_mm", "B_error_mm"]]
    summary = {"synthetic_only": True, "cases": len(rows), "zero_height_measured": len(valid),
               "A_B_MAE_mm": float(np.mean(errors)) if errors else None,
               "A_B_max_error_mm": max(errors) if errors else None,
               "unexpected_failures": sum(row["expected_measurement"] and not row["measured"] for row in rows),
               "unexpected_acceptances": sum(not row["expected_measurement"] and row["measured"] for row in rows),
               "physical_lens_validation": "NOT RUN"}
    summary["maximum_allowed_MAE_mm"] = maximum_mae
    summary["accuracy_passed"] = bool(errors) and summary["A_B_MAE_mm"] <= maximum_mae
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=LOCAL / "synthetic")
    parser.add_argument("--output", type=Path, default=LOCAL / "evaluation")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--max-mae-mm", type=float, default=0.5)
    args = parser.parse_args()
    if args.generate:
        suite(args.dataset)
    summary = evaluate(args.dataset, args.output, args.max_mae_mm)
    print(json.dumps(summary, indent=2))
    if summary["unexpected_failures"] or summary["unexpected_acceptances"] or not summary["accuracy_passed"]:
        sys.exit(1)
