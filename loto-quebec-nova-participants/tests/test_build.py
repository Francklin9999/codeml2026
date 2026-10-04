from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import extraction_is_current, prepare_payload


ROOT = Path(__file__).resolve().parents[1]


class BuildIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extracted = ROOT / "work" / "_local"
        cls.payload = prepare_payload(ROOT / "data", cls.extracted, False)

    def test_extraction_matches_archive_and_is_complete(self):
        self.assertTrue(extraction_is_current(self.extracted, ROOT / "NOVA_ETUDIANTS.zip"))

    def test_payload_has_all_scored_sections(self):
        self.assertEqual(10, len(self.payload["answers"]))
        self.assertEqual(64, len(self.payload["sources"]))
        self.assertTrue(all(self.payload["brief"].get(key) for key in (
            "owner", "dateConditions", "scope", "budget", "priorities", "uncertainties"
        )))

    def test_all_generated_evidence_links_exist_with_anchor(self):
        links = []
        for fact in self.payload["facts"]:
            links.extend(item.get("evidenceHref") for item in fact.get("evidence", []))
        for answer in self.payload["answers"].values():
            links.extend(item.get("evidenceHref") for item in answer.get("sources", []))
        self.assertTrue(links)
        self.assertFalse(any(not link for link in links))
        for link in links:
            relative, anchor = link.split("#", 1)
            content = (self.extracted / relative).read_text(encoding="utf-8")
            self.assertIn(f'id="{anchor}"', content)

    def test_payload_is_json_serializable(self):
        json.dumps(self.payload, ensure_ascii=False, sort_keys=True)

    def test_live_event_updates_every_affected_view_without_touching_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / "data"
            data.mkdir()
            for source in (ROOT / "data").glob("*.json"):
                if source.name not in {"baseline.json"}:
                    shutil.copy2(source, data / source.name)
            events = data / "events"
            events.mkdir()
            shutil.copy2(
                ROOT / "examples" / "event_security_validation.json",
                events / "LIVE-SEC-VALIDATED.json",
            )
            payload = prepare_payload(data, self.extracted, False)
            self.assertEqual(1, len(payload["diff"]))
            self.assertTrue(any(item.get("id") == "LIVE-SEC-VALIDATED" for item in payload["timeline"]))
            self.assertTrue(payload["answers"]["Q08"].get("eventUpdates"))
            action = next(item for item in payload["actions"] if item["id"] == "A-SEC-RETEST")
            self.assertEqual("closed", action["status"])
            condition = next(item for item in payload["brief"]["go_live_conditions"] if item["number"] == 1)
            self.assertEqual("VALIDATED", condition["status"])
            self.assertNotEqual(
                payload["versions"]["baseline"]["hash"],
                payload["versions"]["current"]["hash"],
            )


if __name__ == "__main__":
    unittest.main()
