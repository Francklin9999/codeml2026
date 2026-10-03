"""Check extracted corpus identity and locator coverage without validating claims."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import zipfile


TOP_DIR = "Projet360_NOVA_ETUDIANTS/"


def safe_relative(value):
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a nonempty string")
    relative = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if ("\\" in value or relative.is_absolute() or windows.drive
            or ".." in relative.parts or relative.as_posix() == "."):
        raise ValueError(f"unsafe relative path: {value}")
    return relative.as_posix()


def contained_file(root, relative):
    root = Path(root).resolve()
    target = (root / safe_relative(relative)).resolve()
    if root not in target.parents:
        raise ValueError(f"path escapes root: {relative}")
    return target


def digest(content):
    return hashlib.sha256(content).hexdigest()


def audit(zip_path, local_dir):
    local = Path(local_dir).resolve()
    index = json.loads((local / "files_index.json").read_text(encoding="utf-8"))
    issues = []
    indexed = {}
    for entry in index:
        relative = safe_relative(entry["file"])
        if relative in indexed:
            issues.append(f"duplicate indexed file: {relative}")
        indexed[relative] = entry
    originals = {}
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            relative = member.filename.removeprefix(TOP_DIR)
            relative = safe_relative(relative)
            if relative in originals:
                issues.append(f"duplicate archive member: {relative}")
            originals[relative] = digest(archive.read(member))
    for relative in sorted(originals.keys() - indexed.keys()):
        issues.append(f"unindexed archive member: {relative}")
    for relative in sorted(indexed.keys() - originals.keys()):
        issues.append(f"indexed file absent from archive: {relative}")
    missing_transcriptions = []
    for relative, entry in indexed.items():
        source = contained_file(local / "corpus", relative)
        if not source.is_file():
            issues.append(f"missing extracted source: {relative}")
        elif digest(source.read_bytes()) != originals.get(relative):
            issues.append(f"source differs from archive: {relative}")
        if entry["sha256"] != originals.get(relative):
            issues.append(f"indexed digest differs from archive: {relative}")
        text_path = contained_file(local / "text", relative + ".txt")
        if not text_path.is_file():
            issues.append(f"missing extracted text: {relative}")
        elif source.suffix.lower() == ".png" and "no transcription file yet" in text_path.read_text(encoding="utf-8"):
            missing_transcriptions.append(relative)
    records = [json.loads(line) for line in (local / "locators.jsonl").read_text(encoding="utf-8").splitlines()
               if line.strip()]
    seen = set()
    covered = set()
    for record in records:
        locator = record["id"]
        if locator in seen:
            issues.append(f"duplicate locator: {locator}")
        seen.add(locator)
        if record["file"] not in indexed:
            issues.append(f"locator references unknown file: {locator}")
        covered.add(record["file"])
    uncovered = sorted(set(indexed) - covered)
    attachments = json.loads((local / "attachments_manifest.json").read_text(encoding="utf-8"))
    for attachment in attachments:
        path = contained_file(local / "attachments", attachment["attachment"])
        if not path.is_file() or digest(path.read_bytes()) != attachment["sha256"]:
            issues.append(f"attachment digest mismatch: {attachment['attachment']}")
        for relative in attachment["identical_to_corpus_files"]:
            if originals.get(relative) != attachment["sha256"]:
                issues.append(f"incorrect attachment equivalence: {relative}")
    return {
        "archive_files": len(originals), "indexed_files": len(indexed),
        "locators": len(records), "attachments": len(attachments),
        "attachments_matching_standalone": sum(bool(entry["identical_to_corpus_files"]) for entry in attachments),
        "missing_image_transcriptions": missing_transcriptions,
        "files_without_locators": uncovered, "integrity_issues": issues,
        "semantic_claim_validation": "NOT RUN",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=Path(__file__).resolve().parents[2] / "NOVA_ETUDIANTS.zip")
    parser.add_argument("--local", type=Path, default=Path(__file__).resolve().parents[1] / "_local")
    arguments = parser.parse_args()
    try:
        result = audit(arguments.zip, arguments.local)
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, f"INVALID EXTRACTION: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(bool(result["integrity_issues"]))


if __name__ == "__main__":
    raise SystemExit(main())
