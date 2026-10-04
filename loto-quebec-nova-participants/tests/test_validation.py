import json
import tempfile
import unittest
from pathlib import Path

from nova.validation import validate_data, validate_evidence


class ValidationTests(unittest.TestCase):
    def test_missing_questions_and_unknown_references_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp)
            (data / "facts.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "F-1",
                            "subject": "x",
                            "type": "fact",
                            "statement": "x",
                            "status": "current",
                            "source_file": "x.txt",
                            "locator": "x#1",
                            "quote": "x",
                            "authority": "owner",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (data / "answers.json").write_text(
                json.dumps(
                    {
                        "Q01": {
                            "fact_ids": ["F-MISSING"],
                            "sources": [{"file": "x"}],
                        }
                    }
                ),
                encoding="utf-8",
            )
            errors = validate_data(data)
            self.assertTrue(any("Questions absentes" in error for error in errors))
            self.assertTrue(any("F-MISSING" in error for error in errors))

    def test_evidence_validator_checks_source_locator_and_quote(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            extracted = root / "extracted"
            (extracted / "text").mkdir(parents=True)
            data.mkdir()
            (data / "facts.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "F-OK",
                            "source_file": "source.txt",
                            "locator": "SRC#L1",
                            "quote": "preuve exacte",
                        }
                    ]
                ), encoding="utf-8"
            )
            (extracted / "inventory.json").write_text(
                json.dumps({"sources": [{"path": "source.txt", "text_path": "text/source.txt"}]}),
                encoding="utf-8",
            )
            (extracted / "locators.jsonl").write_text(
                json.dumps({"id": "SRC#L1"}) + "\n", encoding="utf-8"
            )
            (extracted / "text" / "source.txt").write_text(
                "Une preuve exacte dans le corpus.", encoding="utf-8"
            )
            self.assertEqual([], validate_evidence(data, extracted))


if __name__ == "__main__":
    unittest.main()
