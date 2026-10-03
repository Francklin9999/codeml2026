import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf


PAGE_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "Paper Registry"
SOURCE_PDF = PAGE_DIRECTORY / "dossiers_specimen_10_patientes.pdf"
OUTPUT_PATH = Path(__file__).with_name("_local") / "grouped_split_manifest.json"
PAGE_COUNT = 80
PAGES_PER_GROUP = 8
SPLIT_SEED = "dayone-strategy-21-frozen-v1"


def _alpha_tokens(page):
    text = page.get_text("text", sort=True).casefold()
    return {token for token in re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
            if len(token) >= 3}


def verify_page_group_fingerprints(page_words, pages_per_group=PAGES_PER_GROUP):
    if not page_words or len(page_words) % pages_per_group:
        return {"verified": False, "matched_group_headers": 0,
                "distinct_group_signatures": 0, "fully_linked_groups": 0,
                "linked_page_count": 0, "group_page_link_counts": []}

    group_count = len(page_words) // pages_per_group
    first_pages = [page_words[index * pages_per_group] for index in range(group_count)]
    second_pages = [page_words[index * pages_per_group + 1] for index in range(group_count)]
    first_frequency = Counter(token for values in first_pages for token in values)
    second_frequency = Counter(token for values in second_pages for token in values)
    common_token_threshold = max(2, (group_count + 1) // 2)
    common_form_text = {token for token, count in first_frequency.items()
                        if count >= common_token_threshold}
    common_form_text.update(token for token, count in second_frequency.items()
                            if count >= common_token_threshold)
    shared_tokens = [(first & second) - common_form_text
                     for first, second in zip(first_pages, second_pages)]
    token_group_counts = Counter(token for values in shared_tokens for token in values)
    unique_signatures = [frozenset(token for token in values if token_group_counts[token] == 1)
                         for values in shared_tokens]
    matched_groups = sum(bool(signature) for signature in unique_signatures)
    distinct_signatures = len(set(unique_signatures)) - int(frozenset() in unique_signatures)
    group_page_link_counts = [sum(bool(signature & page_words[group_index * pages_per_group + page_offset])
                                  for page_offset in range(pages_per_group))
                              for group_index, signature in enumerate(unique_signatures)]
    fully_linked_groups = sum(count == pages_per_group for count in group_page_link_counts)
    linked_page_count = sum(group_page_link_counts)
    verified = (matched_groups == group_count and distinct_signatures == group_count
                and fully_linked_groups == group_count)
    return {"verified": verified,
            "matched_group_headers": matched_groups,
            "distinct_group_signatures": distinct_signatures,
            "fully_linked_groups": fully_linked_groups,
            "linked_page_count": linked_page_count,
            "group_page_link_counts": group_page_link_counts}


def _pdf_grouping_evidence(document):
    if document.page_count != PAGE_COUNT:
        return {"verified": False, "reason": "unexpected_pdf_page_count",
                "pdf_pages": document.page_count, "matched_group_headers": 0,
                "distinct_group_signatures": 0, "fully_linked_groups": 0,
                "linked_page_count": 0, "group_page_link_counts": []}

    evidence = verify_page_group_fingerprints([_alpha_tokens(page) for page in document])
    evidence["pdf_pages"] = document.page_count
    evidence["reason"] = ("ten distinct group fingerprints linked to all eight pages per block"
                           if evidence["verified"] else
                           "page text does not link every page in each eight-page block to a unique group")
    return evidence


def _source_pages():
    page_files = defaultdict(list)
    for path in PAGE_DIRECTORY.glob("dossiers_specimen_10_patientes-*.png"):
        match = re.search(r"-(\d+)(?:__[^.]*)?\.png$", path.name)
        if match:
            page_files[int(match.group(1))].append(path)
    return page_files


def _group_reference(group_number):
    value = f"synthetic-patient-group-{group_number:02d}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _split_for_group(group_reference):
    ordering = hashlib.sha256(f"{SPLIT_SEED}:{group_reference}".encode("utf-8")).hexdigest()
    return ordering


def audit_page_records(records):
    hash_pages = defaultdict(set)
    hash_groups = defaultdict(set)
    hash_splits = defaultdict(set)
    group_splits = defaultdict(set)
    for record in records:
        group_splits[record["group_ref"]].add(record["split"])
        for digest in set(record["image_sha256"]):
            hash_pages[digest].add(record["page_number"])
            hash_groups[digest].add(record["group_ref"])
            hash_splits[digest].add(record["split"])
    return {
        "duplicate_hashes_across_page_ids": sum(len(page_numbers) > 1
                                                 for page_numbers in hash_pages.values()),
        "duplicate_hashes_across_groups": sum(len(group_refs) > 1 for group_refs in hash_groups.values()),
        "duplicate_hashes_across_splits": sum(len(split_names) > 1 for split_names in hash_splits.values()),
        "page_group_leakage": any(len(split_names) > 1 for split_names in group_splits.values()),
    }


def build_grouped_split():
    with pymupdf.open(SOURCE_PDF) as document:
        evidence = _pdf_grouping_evidence(document)
    page_files = _source_pages()
    expected_pages = set(range(1, PAGE_COUNT + 1))
    inventory_complete = set(page_files) == expected_pages
    file_hashes = {}
    page_records = []
    for page_number in sorted(page_files):
        image_hashes = []
        for path in page_files[page_number]:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            image_hashes.append(digest)
            file_hashes[digest] = file_hashes.get(digest, 0) + 1
        page_records.append({"page_number": page_number,
                             "image_sha256": sorted(set(image_hashes))})

    split_manifest = None
    if evidence["verified"] and inventory_complete:
        groups = sorted((_group_reference(group_number), group_number)
                        for group_number in range(1, 11))
        ordered_groups = sorted(groups, key=lambda item: _split_for_group(item[0]))
        split_by_group = {}
        for index, (group_reference, _) in enumerate(ordered_groups):
            split_by_group[group_reference] = "train" if index < 6 else "development" if index < 8 else "holdout"
        split_manifest = []
        for page_record in page_records:
            group_number = (page_record["page_number"] - 1) // PAGES_PER_GROUP + 1
            group_reference = _group_reference(group_number)
            split_manifest.append({"page_number": page_record["page_number"],
                                   "group_ref": group_reference,
                                   "split": split_by_group[group_reference],
                                   "image_sha256": page_record["image_sha256"]})

    output = {
        "pdf_grouping_evidence": evidence,
        "png_page_inventory_complete": inventory_complete,
        "unique_page_count": len(page_files),
        "png_file_count": sum(len(files) for files in page_files.values()),
        "unique_image_hash_count": len(file_hashes),
        "redundant_exact_png_copies": sum(len(files) - 1 for files in page_files.values()),
        "page_order_mapping_verified": bool(evidence["verified"] and inventory_complete),
        "split_created": split_manifest is not None,
        "page_records": page_records if split_manifest is not None else None,
        "split_manifest": split_manifest,
    }
    if split_manifest is not None:
        output["split_counts"] = {name: sum(record["split"] == name for record in split_manifest)
                                  for name in ("train", "development", "holdout")}
        output["group_counts"] = {name: len({record["group_ref"] for record in split_manifest
                                            if record["split"] == name})
                                  for name in ("train", "development", "holdout")}
        output["duplicate_hash_groups"] = sum(copy_count > 1 for copy_count in file_hashes.values())
        output.update(audit_page_records(split_manifest))
        output["duplicate_copies_stay_with_page"] = (
            output["duplicate_hashes_across_page_ids"] == 0
            and output["duplicate_hashes_across_groups"] == 0
            and output["duplicate_hashes_across_splits"] == 0)
        if output["duplicate_copies_stay_with_page"] and not output["page_group_leakage"]:
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
        else:
            output["split_created"] = False
            output["split_manifest"] = None
            output["page_records"] = None
            output["split_rejection_reason"] = "duplicate image or patient group crosses partition boundaries"
            OUTPUT_PATH.unlink(missing_ok=True)
    else:
        OUTPUT_PATH.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    result = build_grouped_split()
    summary = {key: value for key, value in result.items()
               if key not in ("page_records", "split_manifest")}
    print(json.dumps(summary, indent=2))
