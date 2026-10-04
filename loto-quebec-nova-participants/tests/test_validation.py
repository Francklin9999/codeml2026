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
                json.dumps({"id": "SRC#L1", "file": "source.txt", "text": "preuve exacte"}) + "\n", encoding="utf-8"
            )
            (extracted / "text" / "source.txt").write_text(
                "Une preuve exacte dans le corpus.", encoding="utf-8"
            )
            self.assertEqual([], validate_evidence(data, extracted))

    def test_evidence_validator_binds_locator_to_source_and_unit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            extracted = root / "extracted"
            (extracted / "text").mkdir(parents=True)
            data.mkdir()
            (data / "facts.json").write_text(
                json.dumps([
                    {"id": "F-WRONG-FILE", "source_file": "a.txt", "locator": "B#1", "quote": "preuve"},
                    {"id": "F-WRONG-UNIT", "source_file": "a.txt", "locator": "A#1", "quote": "preuve"},
                ]), encoding="utf-8"
            )
            (extracted / "inventory.json").write_text(
                json.dumps({"sources": [
                    {"path": "a.txt", "text_path": "text/a.txt"},
                    {"path": "b.txt", "text_path": "text/b.txt"},
                ]}), encoding="utf-8"
            )
            (extracted / "locators.jsonl").write_text(
                json.dumps({"id": "A#1", "file": "a.txt", "text": "autre paragraphe"}) + "\n" +
                json.dumps({"id": "B#1", "file": "b.txt", "text": "preuve"}) + "\n",
                encoding="utf-8",
            )
            (extracted / "text" / "a.txt").write_text("preuve ailleurs dans A", encoding="utf-8")
            (extracted / "text" / "b.txt").write_text("preuve", encoding="utf-8")
            errors = validate_evidence(data, extracted)
            self.assertTrue(any("appartient à 'b.txt'" in error for error in errors))
            self.assertTrue(any("introuvable dans l'unité 'A#1'" in error for error in errors))

    def test_evidence_validator_accepts_ticket_timestamp_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            extracted = root / "extracted"
            (extracted / "text").mkdir(parents=True)
            data.mkdir()
            (data / "facts.json").write_text(json.dumps([{
                "id": "F-TICKET", "source_file": "ticket.txt", "locator": "T#2026-09-17T16:10",
                "quote": "17 sept 16:10 - Marc : Validé côté intégration. Je ferme.",
            }]), encoding="utf-8")
            (extracted / "inventory.json").write_text(json.dumps({"sources": [{
                "path": "ticket.txt", "text_path": "text/ticket.txt",
            }]}), encoding="utf-8")
            (extracted / "locators.jsonl").write_text(json.dumps({
                "id": "T#2026-09-17T16:10", "file": "ticket.txt",
                "text": "Marc : Validé côté intégration. Je ferme.",
            }) + "\n", encoding="utf-8")
            (extracted / "text" / "ticket.txt").write_text("source", encoding="utf-8")
            self.assertEqual([], validate_evidence(data, extracted))

    def test_evidence_validator_rejects_duplicate_locator_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            extracted = root / "extracted"
            data.mkdir()
            extracted.mkdir()
            (data / "facts.json").write_text("[]", encoding="utf-8")
            row = json.dumps({"id": "DUP", "file": "x", "text": "x"}) + "\n"
            (extracted / "locators.jsonl").write_text(row + row, encoding="utf-8")
            errors = validate_evidence(data, extracted)
            self.assertIn("locateur dupliqué 'DUP'", errors)


if __name__ == "__main__":
    unittest.main()
