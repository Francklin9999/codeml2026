import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

WORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared import data
from robust_link import fit_link, link_objective, predict_link


class RobustLinkTests(unittest.TestCase):
    def setUp(self):
        generator = np.random.default_rng(2803)
        merit = generator.normal(size=120)
        self.features = pd.DataFrame({"merit": merit, "remote": np.tile([0.0, 1.0], 60),
                                      "income": generator.normal(size=120)})
        self.target = (merit + generator.normal(scale=0.8, size=120) > 0).astype(int)

    def test_analytic_gradient_matches_central_difference(self):
        standardized = self.features.to_numpy(dtype=float)
        target = self.target
        parameters = np.linspace(-0.15, 0.2, standardized.shape[1] + 1)
        _, analytic = link_objective(parameters, standardized, target, 3)
        numerical = np.empty_like(parameters)
        step_size = 1e-6
        for position in range(len(parameters)):
            offset = np.zeros_like(parameters)
            offset[position] = step_size
            upper = link_objective(parameters + offset, standardized, target, 3)[0]
            lower = link_objective(parameters - offset, standardized, target, 3)[0]
            numerical[position] = (upper - lower) / (2 * step_size)
        np.testing.assert_allclose(analytic, numerical, atol=2e-6, rtol=2e-5)

    def test_fit_is_deterministic_and_neutralization_preserves_input(self):
        first = fit_link(self.features, self.target, 3)
        second = fit_link(self.features, self.target, 3)
        np.testing.assert_allclose(first["coefficients"], second["coefficients"], atol=1e-10)
        original = self.features.copy(deep=True)
        probabilities = predict_link(first, self.features, neutralize_region=True)
        self.assertTrue(np.isfinite(probabilities).all())
        pd.testing.assert_frame_equal(self.features, original)
        prediction = data.top_k_mask(probabilities, 40)
        self.assertEqual(int(prediction.sum()), 40)

    def test_invalid_labels_and_regularization_are_rejected_without_truncation(self):
        invalid_target = self.target.astype(float)
        invalid_target[0] = 0.5
        with self.assertRaisesRegex(ValueError, "binary"):
            fit_link(self.features, invalid_target, 3)
        for value in (0, -1, np.nan, np.inf):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "regularization"):
                fit_link(self.features, self.target, 3, regularization_c=value)


if __name__ == "__main__":
    unittest.main()
