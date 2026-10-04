import json
import tempfile
import unittest
from pathlib import Path

from nova.validation import validate_data


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


if __name__ == "__main__":
    unittest.main()

