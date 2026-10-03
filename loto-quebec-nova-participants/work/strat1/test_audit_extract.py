import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from audit_extract import audit, safe_relative


class ExtractionAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.local = self.root / "_local"
        for folder in ("corpus", "text", "attachments"):
            (self.local / folder).mkdir(parents=True)
        self.archive = self.root / "source.zip"
        content = b"Synthetic source"
        self.expected_digest = hashlib.sha256(content).hexdigest()
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("Projet360_NOVA_ETUDIANTS/source.txt", content)
        (self.local / "corpus/source.txt").write_bytes(content)
        (self.local / "text/source.txt.txt").write_text("Synthetic source", encoding="utf-8")
        (self.local / "files_index.json").write_text(json.dumps([
            {"file": "source.txt", "sha256": self.expected_digest}
        ]), encoding="utf-8")
        (self.local / "locators.jsonl").write_text(json.dumps(
            {"id": "source#L1", "file": "source.txt", "text": "Synthetic source"}
        ) + "\n", encoding="utf-8")
        (self.local / "attachments_manifest.json").write_text("[]", encoding="utf-8")

    def test_valid_source_identity_does_not_claim_semantic_validation(self):
        result = audit(self.archive, self.local)
        self.assertEqual(result["integrity_issues"], [])
        self.assertEqual(result["locators"], 1)
        self.assertEqual(result["semantic_claim_validation"], "NOT RUN")

    def test_tampering_and_duplicate_locators_are_detected(self):
        (self.local / "corpus/source.txt").write_bytes(b"Changed")
        locator = (self.local / "locators.jsonl").read_text(encoding="utf-8")
        (self.local / "locators.jsonl").write_text(locator + locator, encoding="utf-8")
        issues = audit(self.archive, self.local)["integrity_issues"]
        self.assertTrue(any("source differs" in issue for issue in issues))
        self.assertTrue(any("duplicate locator" in issue for issue in issues))

    def test_missing_text_and_unknown_locator_source_are_detected(self):
        (self.local / "text/source.txt.txt").unlink()
        (self.local / "locators.jsonl").write_text(json.dumps(
            {"id": "other#L1", "file": "unknown.txt"}
        ), encoding="utf-8")
        issues = audit(self.archive, self.local)["integrity_issues"]
        self.assertTrue(any("missing extracted text" in issue for issue in issues))
        self.assertTrue(any("unknown file" in issue for issue in issues))

    def test_unsafe_paths_are_rejected(self):
        for value in ("../outside", "/absolute", "C:/absolute", "C:relative", "a\\b", "", "."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_relative(value)


if __name__ == "__main__":
    unittest.main()
