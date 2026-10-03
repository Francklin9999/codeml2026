"""Local metrology checks with generated inputs, without any physical-accuracy claim."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared.geometry import dimensions, lens_contour, load_spec
from strat1.scale_check import calibrated_spec
from strat1.synthetic import generate_case
from strat2.measure import measure, parallax_correct, write_svg


class PipelineTests(unittest.TestCase):
    def test_known_boxing_dimensions_and_perimeter(self):
        result = dimensions(lens_contour(50, 50))
        self.assertAlmostEqual(result["A_mm"], 50, places=8)
        self.assertAlmostEqual(result["B_mm"], 50, places=8)
        self.assertAlmostEqual(result["perimeter_mm"], np.pi * 50, places=2)

    def test_parallax_scale_and_invalid_height(self):
        points = lens_contour(50, 36) + [78, 66]
        magnified = np.array([78, 66]) + (points - [78, 66]) * 400 / 397
        np.testing.assert_allclose(parallax_correct(magnified, 400, 3, [78, 66]), points)
        with self.assertRaises(ValueError):
            parallax_correct(points, 3, 3, [78, 66])

    def test_print_scale_adjusts_all_metric_geometry(self):
        spec = load_spec()
        adjusted = calibrated_spec(72.72, spec)
        self.assertAlmostEqual(adjusted["square_mm"], 12.12)
        self.assertAlmostEqual(adjusted["window_mm"][2], 121.2)
        self.assertFalse(spec["nominal_dimensions_verified_physically"])
        with self.assertRaises(ValueError):
            calibrated_spec(float("nan"), spec)

    def test_svg_has_physical_units_and_scale_bar(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "contour.svg"
            write_svg(lens_contour(50, 36), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn('width="56.0000mm"', text)
            self.assertIn("h 50", text)
            self.assertIn("Print at 100%", text)

    def test_tilted_backlit_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            truth = generate_case(folder, "tilted", tilt_x=20, tilt_y=-15)
            result = measure(folder / "tilted.png", folder / "result")
            self.assertLess(abs(result["A_mm"] - truth["A_mm"]), 0.3)
            self.assertLess(abs(result["B_mm"] - truth["B_mm"]), 0.3)
            self.assertGreaterEqual(result["calibration"]["corners"], 20)
            self.assertFalse(result["physically_validated"])
            self.assertEqual(json.loads((folder / "result" / "measurement.json").read_text())["image"], "tilted.png")

    def test_reject_missing_reference_and_empty_window(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            generate_case(folder, "no_markers", markers_present=False)
            with self.assertRaisesRegex(ValueError, "calibration corners"):
                measure(folder / "no_markers.png", folder / "result")
            generate_case(folder, "empty", lens_present=False)
            with self.assertRaises(ValueError):
                measure(folder / "empty.png", folder / "result")


if __name__ == "__main__":
    unittest.main()
