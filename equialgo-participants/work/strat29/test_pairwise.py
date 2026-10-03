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
from pairwise import feature_matrix, fit_pairwise, pairwise_training_data, scores


class PairwiseTests(unittest.TestCase):
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

    def test_feature_matrix_excludes_region_and_pair_sampling_is_repeatable(self):
        sample = self.history.groupby(["region_administrative", data.TARGET_COL],
                                      group_keys=False).head(3)
        first_features, first_target = pairwise_training_data(sample, max_pairs_per_region=2)
        second_features, second_target = pairwise_training_data(sample, max_pairs_per_region=2)
        self.assertFalse(any(name == "remote" or name.startswith("reg_")
                             for name in feature_matrix(sample).columns))
        np.testing.assert_array_equal(first_features.to_numpy(), second_features.to_numpy())
        np.testing.assert_array_equal(first_target, second_target)
        self.assertEqual(int(first_target.sum()), len(first_target) // 2)
        self.assertGreater(len(first_target), 0)

    def test_pairwise_fit_scores_are_finite(self):
        sample = self.history.groupby(["region_administrative", data.TARGET_COL],
                                      group_keys=False).head(20)
        estimator, columns, pair_count = fit_pairwise(sample, max_pairs_per_region=8)
        score_values = scores(estimator, columns, sample)
        self.assertGreater(pair_count, 0)
        self.assertEqual(len(score_values), len(sample))
        self.assertTrue(np.isfinite(score_values).all())


if __name__ == "__main__":
    unittest.main()
