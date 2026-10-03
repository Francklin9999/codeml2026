import unittest

from geometry_experiments import strategy21_experiment, strategy27_export_experiment


class GeometryExperimentTests(unittest.TestCase):
    def test_strategy21_selects_on_development_then_evaluates_frozen_holdout(self):
        result = strategy21_experiment()
        self.assertEqual(result["shapes"], 12)
        self.assertEqual(result["development_shapes"], 8)
        self.assertEqual(result["frozen_holdout_shapes"], [8, 9, 10, 11])
        self.assertEqual(len(result["candidate_grid"]), 12)
        selected = result["selected_development_setting"]
        self.assertIsNotNone(selected)
        self.assertTrue(selected["development_gate"])
        self.assertEqual(len(result["holdout_results"]), 4)
        self.assertEqual({row["partition"] for row in result["holdout_results"]}, {"holdout"})
        self.assertTrue(all(row["density"] == selected["density"]
                            and row["tolerance_mm"] == selected["tolerance_mm"]
                            for row in result["holdout_results"]))
        self.assertTrue(all(row["hausdorff_mm"] <= 0.05
                            and row["extent_drift_mm"] <= 0.1
                            and row["vertex_reduction"] >= 0.3
                            for row in result["holdout_results"]))
        self.assertTrue(all(row["hausdorff_mm"] > 0.05
                            for row in result["high_tolerance_negative_control_0_2mm"]))

    def test_strategy27_export_reload_translation_mirror_and_scale(self):
        result = strategy27_export_experiment()
        for name in ("base_mesh", "stl_reloaded_mesh", "translated_input_mesh",
                     "reflected_and_swapped_mesh"):
            self.assertTrue(all(result[name]["checks"].values()), name)
        self.assertFalse(result["base_generation_metadata"]["physical_fit_validated"])
        self.assertLessEqual(result["translation_dimension_drift_mm"], 0.05)
        self.assertLessEqual(result["translation_volume_relative_drift"], 1e-6)
        self.assertLessEqual(result["stl_reload_dimension_drift_mm"], 0.05)
        self.assertLessEqual(result["stl_reload_volume_relative_drift"], 1e-6)
        self.assertLessEqual(result["mirror_swap_dimension_drift_mm"], 0.05)
        self.assertLessEqual(result["mirror_swap_volume_relative_drift"], 1e-6)
        self.assertEqual([record["factor"] for record in result["scale_sweep"]], [0.8, 1.2, 1.5])
        for record in result["scale_sweep"]:
            self.assertTrue(all(record["reloaded_mesh"]["checks"].values()))
            self.assertFalse(record["generation_metadata"]["physical_fit_validated"])
            self.assertLessEqual(record["dimension_drift_mm"], 0.05)
            self.assertLessEqual(record["bounds_drift_mm"], 0.05)
            self.assertLessEqual(record["volume_relative_drift"], 0.002)
        self.assertFalse(result["left_right_orientation_metadata_available"])


if __name__ == "__main__":
    unittest.main()
