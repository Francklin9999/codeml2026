from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from grouped_split import OUTPUT_PATH, audit_page_records, build_grouped_split, verify_page_group_fingerprints


class GroupedSplitTests(unittest.TestCase):
    def test_split_artifact_is_blocked_when_verified_headers_hide_a_cross_group_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page_files = {}
            for page_number in range(1, 81):
                path = root / f"page_{page_number}.png"
                path.write_bytes(f"synthetic pixels {page_number}".encode("utf-8"))
                page_files[page_number] = [path]
            page_files[9] = page_files[1]
            output = root / "split.json"
            with patch("grouped_split._pdf_grouping_evidence", return_value={"verified": True}), \
                    patch("grouped_split._source_pages", return_value=page_files), \
                    patch("grouped_split.OUTPUT_PATH", output):
                result = build_grouped_split()
            self.assertFalse(result["split_created"])
            self.assertIsNone(result["split_manifest"])
            self.assertEqual(result["duplicate_hashes_across_groups"], 1)
            self.assertFalse(output.exists())

    def test_pdf_page_inventory_is_not_mislabeled_as_a_verified_grouped_split(self):
        result = build_grouped_split()
        evidence = result["pdf_grouping_evidence"]
        self.assertFalse(evidence["verified"])
        self.assertEqual(evidence["pdf_pages"], 80)
        self.assertEqual(evidence["matched_group_headers"], 10)
        self.assertEqual(evidence["distinct_group_signatures"], 10)
        self.assertEqual(evidence["linked_page_count"], 38)
        self.assertEqual(evidence["fully_linked_groups"], 0)
        self.assertTrue(result["png_page_inventory_complete"])
        self.assertEqual(result["unique_page_count"], 80)
        self.assertEqual(result["png_file_count"], 124)
        self.assertEqual(result["unique_image_hash_count"], 80)
        self.assertEqual(result["redundant_exact_png_copies"], 44)
        self.assertFalse(result["split_created"])
        self.assertFalse(result["page_order_mapping_verified"])
        self.assertFalse(OUTPUT_PATH.exists())

    def test_manifest_omits_extracted_pdf_identifiers_and_paths(self):
        result = build_grouped_split()
        self.assertIsNone(result["split_manifest"])

    def test_reordered_middle_page_breaks_all_page_fingerprint_link(self):
        pages = []
        for group_index in range(2):
            for page_index in range(8):
                pages.append({f"patient_{group_index}", "shared_form_header", f"page_{page_index}"})
        intact = verify_page_group_fingerprints(pages, pages_per_group=8)
        self.assertTrue(intact["verified"])
        pages[3], pages[11] = pages[11], pages[3]
        reordered = verify_page_group_fingerprints(pages, pages_per_group=8)
        self.assertFalse(reordered["verified"])
        self.assertEqual(reordered["fully_linked_groups"], 0)

    def test_copied_image_across_groups_and_splits_is_detected(self):
        records = [
            {"page_number": 1, "group_ref": "group_a", "split": "train", "image_sha256": ["shared_hash"]},
            {"page_number": 9, "group_ref": "group_b", "split": "holdout", "image_sha256": ["shared_hash"]},
        ]
        audit = audit_page_records(records)
        self.assertEqual(audit["duplicate_hashes_across_page_ids"], 1)
        self.assertEqual(audit["duplicate_hashes_across_groups"], 1)
        self.assertEqual(audit["duplicate_hashes_across_splits"], 1)

    def test_mismatched_known_page_duplicate_is_detected(self):
        records = [
            {"page_number": 7, "group_ref": "group_a", "split": "train", "image_sha256": ["known_page_hash"]},
            {"page_number": 8, "group_ref": "group_a", "split": "train", "image_sha256": ["known_page_hash"]},
        ]
        audit = audit_page_records(records)
        self.assertEqual(audit["duplicate_hashes_across_page_ids"], 1)
        self.assertEqual(audit["duplicate_hashes_across_groups"], 0)
        self.assertEqual(audit["duplicate_hashes_across_splits"], 0)


if __name__ == "__main__":
    unittest.main()
