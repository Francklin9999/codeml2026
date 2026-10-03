import hashlib
from pathlib import Path, PurePosixPath
from pathlib import PureWindowsPath
import re


REQUIRED_FIELDS = {"path", "sha256", "custodian", "captured_at", "source"}


def verify_manifest(case_root, manifest):
    root = Path(case_root).resolve()
    if not isinstance(manifest, list):
        return ["manifest must be a list"]
    issues = []
    seen_paths = set()
    for index, entry in enumerate(manifest):
        if not isinstance(entry, dict):
            issues.append(f"entry {index}: expected object")
            continue
        missing = sorted(REQUIRED_FIELDS - entry.keys())
        if missing:
            issues.append(f"entry {index}: missing fields {', '.join(missing)}")
            continue
        invalid_text = sorted(field for field in {"path", "custodian", "captured_at", "source"}
                              if not isinstance(entry[field], str) or not entry[field].strip())
        if invalid_text:
            issues.append(f"entry {index}: empty or invalid text fields {', '.join(invalid_text)}")
            continue
        source_path = entry["path"]
        relative = PurePosixPath(source_path)
        windows_relative = PureWindowsPath(source_path)
        target = (root / Path(*relative.parts)).resolve()
        if ("\\" in source_path or relative.is_absolute() or windows_relative.is_absolute()
                or windows_relative.drive or ".." in relative.parts or root not in target.parents):
            issues.append(f"entry {index}: unsafe path")
            continue
        if not isinstance(entry["sha256"], str) or re.fullmatch(r"[0-9a-fA-F]{64}", entry["sha256"]) is None:
            issues.append(f"entry {index}: invalid SHA-256")
            continue
        canonical_path = relative.as_posix().casefold()
        if canonical_path in seen_paths:
            issues.append(f"entry {index}: duplicate path")
            continue
        seen_paths.add(canonical_path)
        symlink_cursor = root
        has_symlink = False
        for part in relative.parts:
            symlink_cursor = symlink_cursor / part
            if symlink_cursor.is_symlink():
                has_symlink = True
                break
        if has_symlink:
            issues.append(f"entry {index}: symlink path")
            continue
        if not target.is_file():
            issues.append(f"entry {index}: missing file {relative.as_posix()}")
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != entry["sha256"].lower():
            issues.append(f"entry {index}: hash mismatch {relative.as_posix()}")
    return issues
