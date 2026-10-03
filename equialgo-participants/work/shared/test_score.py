"""Sanity checks for the hypothetical scorer, not the organisers' hidden score."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared import data
from shared.score import eo_gap, official_like
from shared.validate_submission import validate


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.reference = np.tile([1, 1, 0, 0, 0], 20)
        self.group = np.repeat(["Centre", "Eloignee"], 50)
        self.baseline = np.zeros(100, dtype=int)
        self.baseline[:30] = 1
        self.baseline[50:60] = 1

    def test_perfect_gets_35_for_all_agreement_metrics(self):
        for metric in ["accuracy", "f1", "balanced_accuracy"]:
            result = official_like(self.reference, self.reference, self.group, self.baseline, metric)
            self.assertEqual(result["total"], 35)

    def test_baseline_closes_no_measured_gap(self):
        result = official_like(self.baseline, self.reference, self.group, self.baseline)
        self.assertEqual(result["equity"], 0)

    def test_invalid_budget_and_seed_reproducibility(self):
        prediction = np.zeros(100, dtype=int)
        prediction[:30] = 1
        self.assertEqual(official_like(prediction, self.reference, self.group, self.baseline)["total"], 0)
        prediction[:50] = 1
        self.assertEqual(official_like(prediction, self.reference, self.group, self.baseline)["total"], 0)
        first = official_like(self.baseline, self.reference, self.group, self.baseline, rng=123)
        self.assertEqual(first, official_like(self.baseline, self.reference, self.group, self.baseline, rng=123))

    def test_undefined_group_and_invalid_labels_rejected(self):
        reference = self.reference.copy()
        reference[50:] = 0
        with self.assertRaisesRegex(ValueError, "no reference positives"):
            eo_gap(reference, self.baseline, self.group)
        with self.assertRaises(ValueError):
            official_like(self.baseline + 2, self.reference, self.group, self.baseline)

    def test_top_k_is_exact_and_ties_are_deterministic(self):
        np.testing.assert_array_equal(data.top_k_mask([0.5, 0.5, 0.2], 1, [20, 30, 40]), [0, 1, 0])
        with self.assertRaises(ValueError):
            data.top_k_mask([0.2, 0.3], -1)
        with self.assertRaises(ValueError):
            data.top_k_mask([float("nan")], 1)
        with self.assertRaises(ValueError):
            data.submission_frame([0.9], pd.DataFrame({data.ID_COL: ["C0"]}))

    def test_submission_order_binary_and_budget(self):
        candidates = pd.DataFrame({data.ID_COL: [f"C{number}" for number in range(10)]})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "predictions.csv"
            submission = data.submission_frame([1] * 4 + [0] * 6, candidates)
            submission.to_csv(path, index=False)
            self.assertEqual(validate(path, candidates)[1]["grants"], 4)
            submission.iloc[::-1].to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "row order"):
                validate(path, candidates)
            submission.loc[0, data.TARGET_COL] = 2
            submission.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "only 0 or 1"):
                validate(path, candidates)


if __name__ == "__main__":
    unittest.main()
