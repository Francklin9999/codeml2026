import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
WORK_DIR = HERE.parents[1]
sys.path.insert(0, str(WORK_DIR))
sys.path.insert(0, str(HERE.parent))

from shared import data
from income_forms import FORMS, design, fit_form, predict, restricted_cubic_basis


class IncomeFormTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.TemporaryDirectory()
        rows = []
        for local_row in range(20):
            for region_number, region in enumerate(data.REGIONS):
                rows.append({"id_candidat": f"H{local_row:02d}{region_number}",
                             data.TARGET_COL: local_row % 2,
                             "region_administrative": region,
                             "cote_r_equivalent": 20 + local_row * 0.4 + region_number * 0.1,
                             "revenu_familial_estime": 30000 + local_row * 10000 + region_number * 100,
                             "heures_travail_semaine": 10 + local_row % 30,
                             "distance_domicile_campus_km": 5 + local_row * 3 + region_number,
                             "premiere_generation_universitaire": local_row % 2,
                             "programme_etudes": f"P{local_row % 3}",
                             "code_postal_3": f"A{local_row % 4}"})
        candidate_rows = []
        for local_row in range(10):
            for region_number, region in enumerate(data.REGIONS):
                candidate_rows.append({"id_candidat": f"C{local_row:02d}{region_number}",
                                       "region_administrative": region,
                                       "cote_r_equivalent": 20 + local_row * 0.5 + region_number * 0.1,
                                       "revenu_familial_estime": 35000 + local_row * 10000 + region_number * 100,
                                       "heures_travail_semaine": 12 + local_row % 28,
                                       "distance_domicile_campus_km": 8 + local_row * 4 + region_number,
                                       "premiere_generation_universitaire": local_row % 2,
                                       "programme_etudes": f"P{local_row % 3}",
                                       "code_postal_3": f"A{local_row % 4}"})
        data_directory = Path(cls.data_directory.name)
        pd.DataFrame(rows).to_csv(data_directory / "donnees_demandes.csv", index=False)
        pd.DataFrame(candidate_rows).to_csv(data_directory / "candidats_evaluation.csv", index=False)
        data.set_data_root(data_directory)
        cls.history = data.load_history()

    @classmethod
    def tearDownClass(cls):
        cls.data_directory.cleanup()

    def test_preregistered_income_designs_are_finite_and_aligned(self):
        training = self.history.iloc[:80]
        scoring = self.history.iloc[80:]
        raw_matrix, _ = design(training, "raw")
        np.testing.assert_allclose(raw_matrix["income_raw_per_100k"].to_numpy(),
                                   training["revenu_familial_estime"].to_numpy(dtype=float) / 100000.0)
        for form in FORMS:
            train_matrix, transformer = design(training, form)
            score_matrix, _ = design(scoring, form, transformer)
            self.assertListEqual(list(train_matrix.columns), list(score_matrix.columns))
            self.assertTrue(np.isfinite(train_matrix.to_numpy()).all())
            self.assertTrue(np.isfinite(score_matrix.to_numpy()).all())

    def test_fitted_forms_score_finitely_and_select_exact_quota(self):
        training = self.history.iloc[:80]
        candidates = data.load_candidates().iloc[:40]
        for form in FORMS:
            estimator, columns, transformer = fit_form(training, form)
            probabilities = predict(estimator, columns, transformer, candidates, form,
                                    neutralize_region=True)
            self.assertTrue(np.isfinite(probabilities).all())
            prediction = data.top_k_mask(probabilities, 16, candidates.cote_r_equivalent)
            self.assertEqual(int(prediction.sum()), 16)

    def test_restricted_cubic_spline_has_linear_upper_tail(self):
        knots = np.array([1.0, 2.0, 3.0, 4.0])
        values = np.array([5.0, 6.0, 7.0])
        basis = restricted_cubic_basis(values, knots)
        np.testing.assert_allclose(basis[2] - basis[1], basis[1] - basis[0])


if __name__ == "__main__":
    unittest.main()
