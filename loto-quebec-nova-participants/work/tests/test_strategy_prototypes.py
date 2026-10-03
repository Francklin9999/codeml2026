import hashlib
import importlib.util
import json
from datetime import timedelta
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch


WORK = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = WORK / "_local" / "unittest_fixtures"


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


offline_check = load_module("test_offline_bundle_check", WORK / "strat26" / "offline_bundle_check.py")
time_audit = load_module("test_time_audit", WORK / "strat27" / "time_audit.py")
alias_register = load_module("test_entity_alias_register", WORK / "strat35" / "entity_alias_register.py")
restore_check = load_module(
    "test_restore_manifest_check",
    REPOSITORY / "propolys-participants" / "work" / "strat21" / "restore_manifest_check.py",
)
custody_check = load_module(
    "test_custody_manifest_check",
    REPOSITORY / "propolys-participants" / "work" / "strat28" / "custody_manifest_check.py",
)


class FixtureTestCase(unittest.TestCase):
    def validate_fixture_path(self):
        root = FIXTURE_ROOT.resolve()
        if WORK.resolve() not in root.parents or self.fixture.resolve().parent != root or self.fixture.is_symlink():
            raise ValueError("fixture cleanup target escapes the test workspace")

    def setUp(self):
        if WORK.resolve() not in FIXTURE_ROOT.resolve().parents:
            raise ValueError("fixture root escapes the test workspace")
        FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
        self.fixture = FIXTURE_ROOT / self._testMethodName
        self.validate_fixture_path()
        if self.fixture.exists():
            shutil.rmtree(self.fixture)
        self.fixture.mkdir()

    def tearDown(self):
        self.validate_fixture_path()
        shutil.rmtree(self.fixture, ignore_errors=True)


class OfflineBundleCheckTests(FixtureTestCase):
    def write_bundle(self, files):
        for relative, content in files.items():
            target = self.fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        entries = [
            {"path": relative, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}
            for relative, content in files.items()
        ]
        (self.fixture / "manifest.json").write_text(
            json.dumps({"files": entries}), encoding="utf-8"
        )

    def test_hash_inventory_and_local_html_query_fragment(self):
        self.write_bundle({
            "evidence.txt": "synthetic evidence",
            "icon.svg": "<svg></svg>",
            "index.html": '<a href="evidence.txt?view=full#proof">Evidence</a><img src="icon.svg#mark">',
        })
        self.assertEqual(offline_check.verify_bundle(self.fixture), [])

    def test_changed_missing_and_unlisted_files_are_reported(self):
        self.write_bundle({"evidence.txt": "synthetic evidence"})
        (self.fixture / "evidence.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(offline_check.verify_bundle(self.fixture), ["hash mismatch: evidence.txt"])
        (self.fixture / "evidence.txt").unlink()
        self.assertEqual(offline_check.verify_bundle(self.fixture), ["missing: evidence.txt"])
        (self.fixture / "extra.txt").write_text("extra", encoding="utf-8")
        self.assertEqual(offline_check.verify_bundle(self.fixture), ["missing: evidence.txt", "unlisted: extra.txt"])

    def test_unsafe_duplicate_and_invalid_manifest_paths_are_reported(self):
        self.write_bundle({})
        entries = [
            {"path": "..\\outside.txt", "sha256": "0" * 64},
            {"path": "duplicate.txt", "sha256": "0" * 64},
            {"path": "duplicate.txt", "sha256": "1" * 64},
            {"path": "bad-hash.txt", "sha256": "not-a-digest"},
        ]
        (self.fixture / "manifest.json").write_text(
            json.dumps({"files": entries}), encoding="utf-8"
        )
        issues = offline_check.verify_bundle(self.fixture)
        self.assertIn("unsafe path: ..\\outside.txt", issues)
        self.assertIn("duplicate path: duplicate.txt", issues)
        self.assertIn("invalid SHA-256: bad-hash.txt", issues)

    def test_html_external_unsafe_and_missing_links_are_reported(self):
        self.write_bundle({
            "index.html": '<a href="https://example.test">remote</a>'
                          '<a href="../outside.txt">unsafe</a>'
                          '<img src="missing.png">',
        })
        issues = offline_check.verify_bundle(self.fixture)
        self.assertIn("external URL in index.html: https://example.test", issues)
        self.assertIn("unsafe link in index.html: ../outside.txt", issues)
        self.assertIn("missing link target in index.html: missing.png", issues)

    def test_malformed_urls_and_null_encoded_paths_are_reported(self):
        self.write_bundle({"index.html": '<a href="http://[invalid">bad</a><a href="%00.txt">null</a>'})
        issues = offline_check.verify_bundle(self.fixture)
        self.assertTrue(any("invalid URL" in issue for issue in issues))
        self.assertIn("invalid link path in index.html", issues)

    def test_symlinked_bundle_file_is_rejected(self):
        bundle = self.fixture / "bundle"
        bundle.mkdir()
        link = bundle / "outside.txt"
        link.write_text("synthetic link target", encoding="utf-8")
        entry = {
            "path": "outside.txt",
            "sha256": hashlib.sha256(link.read_bytes()).hexdigest(),
        }
        (bundle / "manifest.json").write_text(
            json.dumps({"files": [entry]}), encoding="utf-8"
        )
        is_link = lambda path: path == link
        with patch.object(Path, "is_symlink", autospec=True, side_effect=is_link):
            issues = offline_check.verify_bundle(bundle)
        self.assertIn("symlink path: outside.txt", issues)
        self.assertIn("symlink file: outside.txt", issues)

    def test_cli_reports_pass_or_fail_without_fetching_urls(self):
        self.write_bundle({"index.html": "<main>offline</main>"})
        command = [sys.executable, str(WORK / "strat26" / "offline_bundle_check.py"), str(self.fixture)]
        valid = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(valid.returncode, 0)
        self.assertIn("PASS", valid.stdout)
        self.write_bundle({"index.html": '<a href="https://example.test">remote</a>'})
        invalid = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("external URL", invalid.stdout)


class TimestampPrecisionTests(unittest.TestCase):
    def test_interval_width_tracks_source_precision(self):
        for value, precision, width, source_zone in [
            ("2026-09-30T09", "hour", timedelta(hours=1), "America/Toronto"),
            ("2026-09-30T09:00", "minute", timedelta(minutes=1), "America/Toronto"),
            ("2026-09-30T09:00:00Z", "second", timedelta(seconds=1), None),
            ("2026-09-30T09:00:00.12Z", "fractional-second", timedelta(milliseconds=10), None),
        ]:
            with self.subTest(value=value):
                result = time_audit.parse_timestamp(value, source_zone)
                self.assertEqual(result.precision, precision)
                self.assertEqual(result.end_exclusive - result.start_inclusive, width)

    def test_date_only_is_an_unzoned_day_interval(self):
        result = time_audit.parse_timestamp("2026-09-30")
        self.assertEqual(result.precision, "day")
        self.assertEqual(result.end_exclusive - result.start_inclusive, timedelta(days=1))
        self.assertIsNone(result.start_inclusive.tzinfo)
        self.assertIsNone(result.end_exclusive.tzinfo)

    def test_local_dst_transition_and_uncertain_fold_or_gap(self):
        before_jump = time_audit.parse_timestamp("2026-03-08T01:59", "America/Toronto")
        after_jump = time_audit.parse_timestamp("2026-03-08T03:00", "America/Toronto")
        self.assertEqual(before_jump.start_inclusive.utcoffset(), timedelta(0))
        self.assertEqual(before_jump.end_exclusive - before_jump.start_inclusive, timedelta(minutes=1))
        self.assertEqual(before_jump.end_exclusive, after_jump.start_inclusive)
        folded = time_audit.parse_timestamp("2026-11-01T01:30", "America/Toronto")
        gap = time_audit.parse_timestamp("2026-03-08T02:30", "America/Toronto")
        self.assertIsNone(folded.start_inclusive)
        self.assertIsNone(gap.start_inclusive)

    def test_missing_or_unsupported_timezone_forms_are_not_guessed(self):
        for value, zone in [
            ("2026-09-30T09:00", None),
            ("09/30/26", None),
            ("2026-09-30 09:00:00Z", None),
            ("2026-09-30T09:00:00.1234567Z", None),
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                time_audit.parse_timestamp(value, zone)


class RestoreManifestCheckTests(unittest.TestCase):
    def valid_record(self):
        return {
            "service_id": "svc-demo",
            "backup_job_id": "job-demo",
            "restore_started_at": "2026-01-01T00:00:00Z",
            "restore_completed_at": "2026-01-01T00:01:00Z",
            "integrity_status": "verified",
            "integrity_evidence": "synthetic-hash-record",
            "dependency_status": "clear",
            "owner_signoff": "signed",
            "owner_id": "synthetic-owner",
            "evidence_source": "synthetic-log.txt",
        }

    def test_complete_synthetic_record_passes_completeness_check(self):
        self.assertEqual(restore_check.check_restore_record(self.valid_record()), [])

    def test_nonstring_and_unsupported_claims_are_rejected_without_crash(self):
        record = self.valid_record()
        record.update({"owner_signoff": True, "integrity_status": False, "owner_id": ""})
        issues = restore_check.check_restore_record(record)
        self.assertIn("invalid fields: integrity_status, owner_signoff", issues)
        record = self.valid_record()
        record.update({"integrity_evidence": "", "owner_id": None})
        self.assertIn("verified integrity lacks supporting evidence", restore_check.check_restore_record(record))
        self.assertIn("owner sign-off lacks owner identity", restore_check.check_restore_record(record))

    def test_timestamp_order_and_explicit_offsets_are_checked(self):
        record = self.valid_record()
        record.update({
            "restore_started_at": "2026-01-01T00:02:00Z",
            "restore_completed_at": "2026-01-01T00:01:00Z",
        })
        self.assertIn("restore completion precedes start", restore_check.check_restore_record(record))
        record["restore_started_at"] = "2026-01-01T00:02:00"
        self.assertIn("restore times require explicit timezone offsets", restore_check.check_restore_record(record))


class CustodyManifestCheckTests(FixtureTestCase):
    def make_entry(self, relative_path="artifact.bin"):
        content = b"synthetic evidence"
        (self.fixture / relative_path).write_bytes(content)
        return {
            "path": relative_path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "custodian": "synthetic operator",
            "captured_at": "2026-01-01T00:00:00Z",
            "source": "synthetic fixture",
        }

    def test_matching_hash_passes_and_changed_hash_fails(self):
        entry = self.make_entry()
        self.assertEqual(custody_check.verify_manifest(self.fixture, [entry]), [])
        (self.fixture / "artifact.bin").write_bytes(b"changed")
        self.assertIn("entry 0: hash mismatch artifact.bin",
                      custody_check.verify_manifest(self.fixture, [entry]))

    def test_path_metadata_and_digest_validation(self):
        entry = self.make_entry()
        for unsafe_path in ["../outside.bin", "..\\outside.bin", "C:/outside.bin"]:
            with self.subTest(path=unsafe_path):
                self.assertIn("entry 0: unsafe path",
                              custody_check.verify_manifest(self.fixture, [dict(entry, path=unsafe_path)]))
        self.assertIn("entry 0: empty or invalid text fields custodian",
                      custody_check.verify_manifest(self.fixture, [dict(entry, custodian=" ")]))
        self.assertIn("entry 0: invalid SHA-256",
                      custody_check.verify_manifest(self.fixture, [dict(entry, sha256="bad")]))

    def test_duplicate_canonical_paths_are_rejected(self):
        entry = self.make_entry()
        duplicate = dict(entry, path="./artifact.bin")
        issues = custody_check.verify_manifest(self.fixture, [entry, duplicate])
        self.assertIn("entry 1: duplicate path", issues)

    def test_symlinked_custody_path_is_rejected(self):
        link = self.fixture / "alias.bin"
        link.write_bytes(b"synthetic evidence")
        entry = {
            "path": "alias.bin",
            "sha256": hashlib.sha256(link.read_bytes()).hexdigest(),
            "custodian": "synthetic operator",
            "captured_at": "2026-01-01T00:00:00Z",
            "source": "synthetic fixture",
        }
        is_link = lambda path: path == link
        with patch.object(Path, "is_symlink", autospec=True, side_effect=is_link):
            issues = custody_check.verify_manifest(self.fixture, [entry])
        self.assertIn("entry 0: symlink path", issues)

    def test_manifest_hash_is_consistency_only_not_a_trust_anchor(self):
        entry = self.make_entry()
        (self.fixture / "artifact.bin").write_bytes(b"replacement")
        entry["sha256"] = hashlib.sha256(b"replacement").hexdigest()
        self.assertEqual(custody_check.verify_manifest(self.fixture, [entry]), [])

    def test_nonlist_manifest_is_rejected(self):
        for value in (None, {}, "artifact"):
            with self.subTest(value=value):
                self.assertEqual(custody_check.verify_manifest(self.fixture, value), ["manifest must be a list"])


class EntityAliasRegisterTests(unittest.TestCase):
    def alias(self, text, reviewed=True, locator="fixture:1", reviewer="reviewer-a"):
        return {
            "text": text,
            "reviewed": reviewed,
            "locator": locator,
            "reviewer": reviewer,
            "confidence": "high",
        }

    def entity(self, entity_id, label, aliases):
        return {"entity_id": entity_id, "preferred_label": label, "aliases": aliases}

    def test_reviewed_exact_alias_resolves_case_insensitively(self):
        register = [self.entity("project-1", "Northstar Project", [self.alias("Northstar")])]
        result = alias_register.resolve_alias(" northSTAR ", register)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["candidates"][0]["entity_id"], "project-1")

    def test_collision_remains_ambiguous_and_is_not_merged(self):
        register = [
            self.entity("project-1", "Northstar Project", [self.alias("Nova")]),
            self.entity("ticket-2", "NOVA-2", [self.alias("Nova", locator="fixture:2")]),
        ]
        result = alias_register.resolve_alias("Nova", register)
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual({candidate["entity_id"] for candidate in result["candidates"]},
                         {"project-1", "ticket-2"})

    def test_unreviewed_collision_blocks_an_existing_reviewed_match(self):
        register = [
            self.entity("project-1", "Northstar", [self.alias("Nova")]),
            self.entity("project-2", "Other Project", [self.alias("Nova", reviewed=False)]),
        ]
        result = alias_register.resolve_alias("Nova", register)
        self.assertEqual(result["status"], "review-required")
        self.assertEqual(result["candidates"][0]["entity_id"], "project-1")

    def test_unreviewed_unlocated_low_confidence_and_fuzzy_matches_do_not_resolve(self):
        register = [
            self.entity("person-1", "Sam Lee", [self.alias("Sam Lee", reviewed=False)]),
            self.entity("person-2", "Samantha Lee", [self.alias("Samantha Lee", locator="", reviewer="")]),
            self.entity("person-3", "Samuel Lee", [dict(self.alias("Samuel Lee"), confidence="medium")]),
        ]
        self.assertEqual(alias_register.resolve_alias("Sam Lee", register)["status"], "review-required")
        self.assertEqual(alias_register.resolve_alias("Samantha Lee", register)["status"], "review-required")
        self.assertEqual(alias_register.resolve_alias("Samuel Lee", register)["status"], "review-required")
        self.assertEqual(alias_register.resolve_alias("Sam L.", register)["status"], "unmatched")


if __name__ == "__main__":
    unittest.main()
