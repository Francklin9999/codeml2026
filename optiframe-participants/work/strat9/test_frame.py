import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon

from frame import build_frame, validate_mesh


def oval(width, height, samples=96):
    angles = np.linspace(0, 2 * np.pi, samples, endpoint=False)
    return np.column_stack((width / 2 * np.cos(angles), height / 2 * np.sin(angles)))


def rounded_rect(width, height, samples=96):
    angles = np.linspace(0, 2 * np.pi, samples, endpoint=False)
    return np.column_stack((width / 2 * np.sign(np.cos(angles)) * abs(np.cos(angles)) ** 0.6,
                            height / 2 * np.sign(np.sin(angles)) * abs(np.sin(angles)) ** 0.6))


class FrameTests(unittest.TestCase):
    def test_asymmetric_contours_produce_valid_single_mesh(self):
        mesh = build_frame(oval(50, 36), rounded_rect(52, 34), {"bridge_width": 18})
        checks = validate_mesh(mesh)
        self.assertTrue(all(checks.values()))

    def test_alternate_bridge_and_clearance_parameters(self):
        mesh = build_frame(rounded_rect(48, 32), oval(51, 37),
                           {"bridge_width": 22, "clearance": 0.3, "rim_width": 4.5})
        self.assertTrue(validate_mesh(mesh)["single_body"])

    def test_rejects_self_intersecting_contour(self):
        bowtie = [[0, 0], [10, 10], [0, 10], [10, 0]]
        with self.assertRaisesRegex(ValueError, "invalid"):
            build_frame(bowtie, oval(50, 36))

    def test_rejects_invalid_parameters(self):
        for parameters in ({"clearance": 0}, {"thickness": 1}, {"lip": 4},
                           {"bridge_width": float("nan")}, {"typo": 4},
                           {"thickness": 2, "pin_diameter": 2.5}, [1, 2]):
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                build_frame(oval(50, 36), oval(50, 36), parameters)

    def test_cli_missing_input_returns_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            result = subprocess.run([
                sys.executable, str(Path(__file__).with_name("frame.py")),
                str(directory / "missing_left.json"), str(directory / "missing_right.json"),
                str(directory / "frame.stl"),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Cannot generate frame:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_board_offset_measurement_json_cli_and_apertures(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            left = directory / "left.json"
            right = directory / "right.json"
            output = directory / "frame.stl"
            left_contour = oval(50, 36) + [81, 66]
            right_contour = rounded_rect(52, 34) + [143, 68]
            left.write_text(json.dumps({"contour_mm": left_contour.tolist()}), encoding="utf-8")
            right.write_text(json.dumps({"contour_mm": right_contour.tolist()}), encoding="utf-8")
            completed = subprocess.run([sys.executable, str(Path(__file__).with_name("frame.py")),
                                        str(left), str(right), str(output)],
                                       check=True, capture_output=True, text=True)
            result = json.loads(completed.stdout)
            mesh = trimesh.load(output, force="mesh")
            self.assertTrue(result["watertight"])
            self.assertTrue(validate_mesh(mesh)["single_body"])
            self.assertAlmostEqual(float(mesh.bounds[:, 1].mean()), 0, places=5)
            left_box_x = -9
            right_box_x = 9
            expected_temporal_left = -9 - 50
            expected_temporal_right = 9 + 52
            self.assertLess(float(mesh.bounds[0, 0]), expected_temporal_left - 4)
            self.assertGreater(float(mesh.bounds[1, 0]), expected_temporal_right + 4)
            section = mesh.section(plane_origin=[0, 0, 2], plane_normal=[0, 0, 1])
            loops = [Polygon(path[:, :2]) for path in section.discrete]
            cavity_loops = sorted(loops, key=lambda polygon: polygon.area)[:-1]
            for distance in (1, 2, 3):
                with self.subTest(nasal_inset_mm=distance):
                    self.assertTrue(any(polygon.contains(Point(left_box_x - distance, 0))
                                        for polygon in cavity_loops))
                    self.assertTrue(any(polygon.contains(Point(right_box_x + distance, 0))
                                        for polygon in cavity_loops))


if __name__ == "__main__":
    unittest.main()
