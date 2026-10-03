import sys
import subprocess
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from eval import evaluate, values_match
from shared.eval import evaluate as evaluate_as_package


def field(key, value, status="CONNU", **extra):
    return {"key": key, "value": value, "status": status, **extra}


class EvaluationTests(unittest.TestCase):
    def test_future_short_year_and_numeric_tolerance_boundary(self):
        self.assertTrue(values_match("pregnancy.edd", field("pregnancy.edd", "01/01/27"),
                                     field("pregnancy.edd", "2027-01-01")))
        self.assertTrue(values_match("newborn.weight", field("newborn.weight", "3.0 kg"),
                                     field("newborn.weight", "3.1 kg")))
        with self.assertRaisesRegex(ValueError, "positive integer"):
            evaluate([], [], bins=0)

    def test_date_number_tolerance_bp_and_enum_comparisons(self):
        self.assertTrue(values_match("delivery.date", field("x", "03/04/2024"), field("x", "2024-04-03")))
        self.assertTrue(values_match("newborn.weight", field("x", "3.0 kg"), field("x", "3.08 kg")))
        self.assertFalse(values_match("newborn.weight", field("x", "3.0 kg"), field("x", "3.11 kg")))
        self.assertFalse(values_match("newborn.weight", field("x", "70/80"), field("x", "70")))
        self.assertFalse(values_match("newborn.weight", field("x", "70 kg"), field("x", "70 g")))
        self.assertFalse(values_match("newborn.weight", field("x", "NaN"), field("x", "NaN")))
        self.assertTrue(values_match("mother.ta", field("x", "120/80"), field("x", "120 / 80", type="blood_pressure")))
        self.assertTrue(values_match("exam.result", field("x", "RAS"), field("x", "Normal(e)s")))

    def test_missing_wrong_status_extra_key_and_privacy_leak(self):
        gt = [{"patient_ref": "a1b2c3d4", "page_type": 3, "fields": [
            field("pregnancy.ddr", "01/01/2024", type="date"),
            field("pregnancy.rh", None, "NON_FOURNI"),
        ]}]
        pred = [{"patient_ref": "a1b2c3d4", "page_type": 3, "fields": [
            field("pregnancy.rh", "positive"),
            field("patient.cin", "12345678"),
        ]}]
        result = evaluate(gt, pred)
        self.assertEqual(result["fields"]["correct"], 0)
        self.assertEqual(result["status"]["accuracy"], 0.0)
        self.assertEqual(result["hallucinations"]["count"], 1)
        self.assertEqual(result["identifier_leaks"], 1)
        self.assertEqual(len(result["extras"]), 1)

    def test_confidence_ece_and_status_confusion(self):
        gt = [{"patient_ref": "r", "page_type": 1, "fields": [field("profile.age", 30)]}]
        pred = [{"patient_ref": "r", "page_type": 1, "fields": [field("profile.age", 31, confidence=0.8)]}]
        result = evaluate(gt, pred)
        self.assertEqual(result["calibration"]["count"], 1)
        self.assertAlmostEqual(result["calibration"]["ece"], 0.8)
        self.assertEqual(result["status"]["confusion"]["CONNU"]["CONNU"], 1)

    def test_extra_prediction_page_and_duplicate_identities(self):
        gt = [{"patient_ref": "a1b2c3d4", "page_type": 1, "fields": []}]
        prediction = [{"patient_ref": "a1b2c3d4", "page_type": 1, "fields": []},
                      {"patient_ref": "e5f6a7b8", "page_type": 2, "fields": [field("patient.cin", "private")] }]
        result = evaluate(gt, prediction)
        self.assertEqual(result["extra_prediction_pages"], 1)
        self.assertEqual(result["identifier_leaks"], 1)
        with self.assertRaisesRegex(ValueError, "duplicate prediction page identity"):
            evaluate(gt, [prediction[0], prediction[0]])
        with self.assertRaisesRegex(ValueError, "duplicate ground-truth page identity"):
            evaluate([gt[0], gt[0]], [])

    def test_duplicate_field_keys_rejected(self):
        page = {"patient_ref": "random1", "page_type": 1,
                "fields": [field("profile.age", 30), field("profile.age", 31)]}
        with self.assertRaisesRegex(ValueError, "duplicate field key"):
            evaluate([page], [page])

    def test_ground_truth_identifier_and_empty_set_rejected(self):
        with self.assertRaisesRegex(ValueError, "identifier-like"):
            evaluate([{"patient_ref": "a1b2c3d4", "page_type": 1,
                       "fields": [field("patient.cin", "redacted")]}], [])
        with self.assertRaisesRegex(ValueError, "empty"):
            evaluate([], [])

    def test_package_import_and_forbidden_prediction_key(self):
        gt = [{"patient_ref": "a1b2c3d4", "page_type": 1, "fields": [field("profile.age", 30)]}]
        pred = [{"patient_ref": "a1b2c3d4", "page_type": 1,
                 "fields": [field("profile.age", 30), field("husband_name", "redacted")]}]
        result = evaluate_as_package(gt, pred)
        self.assertEqual(result["identifier_leaks"], 1)

    def test_unknown_breakdown_is_rejected(self):
        script = Path(__file__).resolve().parents[1] / "eval.py"
        result = subprocess.run([sys.executable, str(script), "--pred", ".", "--gt", ".", "--by", "unknown"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported breakdown", result.stderr)

    def test_schema_rejects_duplicate_keys_and_invalid_page_link(self):
        from schema import ClinicalField, Page
        first = ClinicalField(key="profile.age", value=30, status="CONNU", page_type=1)
        second = ClinicalField(key="profile.age", value=31, status="CONNU", page_type=1)
        with self.assertRaises(ValueError):
            Page(page_type=1, patient_ref="a1b2c3d4", fields=[first, second])
        with self.assertRaises(ValueError):
            Page(page_type=2, patient_ref="a1b2c3d4", fields=[first])
        with self.assertRaises(ValueError):
            Page(page_type=1, patient_ref="Jane Smith", fields=[])
        with self.assertRaises(ValueError):
            ClinicalField(key="patient_name", value="redacted", status="CONNU", page_type=1)


if __name__ == "__main__":
    unittest.main()
