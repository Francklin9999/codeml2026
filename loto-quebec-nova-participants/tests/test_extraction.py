from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from nova.extraction import extract_corpus


ROOT = Path(__file__).resolve().parents[1]


class CorpusExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "out"
        cls.sources_path = Path(cls.temp.name) / "sources.json"
        cls.report = extract_corpus(ROOT / "NOVA_ETUDIANTS.zip", cls.output, cls.sources_path)
        cls.sources = json.loads(cls.sources_path.read_text(encoding="utf-8"))
        cls.locators = [json.loads(line) for line in (cls.output / "locators.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.by_id = {item["id"]: item for item in cls.locators}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_manifest_and_inventory_cover_all_64_files(self) -> None:
        self.assertEqual(64, self.report["source_count"])
        self.assertEqual(64, len(self.sources))
        self.assertEqual(64, len({item["path"] for item in self.sources}))
        self.assertTrue(all(item["classification"] and item["extraction_status"] == "ok" for item in self.sources))
        self.assertEqual(
            ["Manifest size differs for README.txt: declared=7103, actual=5741"],
            self.report["warnings"],
        )

    def test_every_supported_format_is_extracted(self) -> None:
        expected = {".eml", ".pdf", ".xlsx", ".txt", ".csv", ".md", ".png"}
        self.assertEqual(expected, {item["extension"] for item in self.sources})
        self.assertGreaterEqual(self.report["locator_count"], 150)
        self.assertEqual(8, sum(item["classification"] == "image-only-evidence" for item in self.sources))
        self.assertTrue(all((self.output / item["text_path"]).is_file() for item in self.sources))
        self.assertTrue(all((self.output / item["evidence_path"]).is_file() for item in self.sources))

    def test_key_precise_locators(self) -> None:
        required = {
            "M04@15:22",
            "SEC-210#2026-09-19T10:22",
            "SEC-210#header",
            "INV-003.pdf#p1",
            "Registre_Risques_29sept.xlsx!H2",
            "Teams_19sept_Securite@10:31",
            "E05#headers",
            "E05#body",
            "OPS-601_runbook.png#step4",
        }
        self.assertFalse(required - self.by_id.keys(), required - self.by_id.keys())
        for locator in required:
            evidence = self.output / self.by_id[locator]["evidence_file"]
            self.assertIn(f'id="{self.by_id[locator]["anchor"]}"', evidence.read_text(encoding="utf-8"))

    def test_email_attachments_are_saved_and_matched(self) -> None:
        attachments = list((self.output / "attachments").iterdir())
        self.assertEqual(5, len(attachments))
        inv = next(item for item in self.sources if item["path"].endswith("INV-003.pdf"))
        self.assertTrue(inv.get("attachment_copies"))

    def test_pngs_are_copied_with_transcription_contract(self) -> None:
        self.assertEqual(8, len(list((self.output / "images").glob("*.png"))))
        self.assertEqual(8, len(list((self.output / "transcriptions").glob("*.transcription.md"))))
        runbook = (self.output / "transcriptions" / "OPS-601_runbook.png.transcription.md").read_text(encoding="utf-8")
        self.assertIn("Vérifier la santé des services — OK", runbook)
        self.assertIn("Activer le mode maintenance — OK", runbook)
        self.assertIn("Déployer la version approuvée — OK", runbook)
        self.assertIn("retour arrière — TODO", runbook)
        self.assertIn("À compléter", runbook)
        image_sources = [item for item in self.sources if item["extension"] == ".png"]
        self.assertEqual(1, sum(item["transcription_status"] == "verified" for item in image_sources))
        self.assertEqual(7, sum(item["transcription_status"] == "expected" for item in image_sources))

    def test_known_noise_and_duplicates_are_explicit(self) -> None:
        classes = {item["path"]: item["classification"] for item in self.sources}
        self.assertEqual("other-project", classes["08_Archives_et_documents_connexes/INV-778_Projet_ORION.pdf"])
        self.assertEqual("exact-duplicate", classes["08_Archives_et_documents_connexes/Courriel_archive_17sept.eml"])
        self.assertEqual("derived/stale", classes["04_Documents_projet/Registre_Risques_29sept.xlsx"])
        self.assertEqual(5, sum(value == "attachment-copy" for value in classes.values()))

    def test_unsupported_input_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "unsupported.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("Projet360_NOVA_ETUDIANTS/unsupported.bin", b"not evidence")
            with self.assertRaisesRegex(ValueError, "Unsupported corpus format"):
                extract_corpus(archive, Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
