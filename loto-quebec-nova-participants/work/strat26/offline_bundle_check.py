import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import unquote, urlsplit


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attributes):
        for name, value in attributes:
            if name.casefold() in {"href", "src"} and value:
                self.links.append(value.strip())


def verify_bundle(bundle_path):
    bundle = Path(bundle_path).resolve()
    if not bundle.is_dir():
        return ["bundle directory missing"]
    manifest_path = bundle / "manifest.json"
    if manifest_path.is_symlink() or bundle not in manifest_path.resolve().parents:
        return ["unsafe manifest path"]
    if not manifest_path.is_file():
        return ["manifest missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ["manifest is unreadable or invalid JSON"]
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        return ["manifest files must be a list"]
    expected = {}
    issues = []

    for entry in manifest.get("files", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            issues.append("invalid manifest entry path")
            continue
        source_path = entry["path"]
        relative = PurePosixPath(source_path)
        windows_relative = PureWindowsPath(source_path)
        if (not source_path.strip() or "\x00" in source_path or "\\" in source_path
                or relative.is_absolute() or windows_relative.is_absolute()
                or windows_relative.drive or ".." in relative.parts
                or relative.as_posix() == "manifest.json"):
            issues.append(f"unsafe path: {entry['path']}")
            continue
        digest = entry.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(
                character not in "0123456789abcdefABCDEF" for character in digest):
            issues.append(f"invalid SHA-256: {source_path}")
            continue
        key = relative.as_posix()
        if key in expected:
            issues.append(f"duplicate path: {key}")
            continue
        expected[key] = digest.lower()

    package_paths = list(bundle.rglob("*"))
    for path in package_paths:
        if path.is_symlink():
            issues.append(f"symlink path: {path.relative_to(bundle).as_posix()}")
    actual = {
        path.relative_to(bundle).as_posix()
        for path in package_paths
        if path.is_file() and path != manifest_path
    }
    for relative in sorted(expected.keys() - actual):
        issues.append(f"missing: {relative}")
    for relative in sorted(actual - expected.keys()):
        issues.append(f"unlisted: {relative}")
    for relative in sorted(expected.keys() & actual):
        target = (bundle / relative).resolve()
        if bundle not in target.parents:
            issues.append(f"unsafe file target: {relative}")
            continue
        if (bundle / relative).is_symlink():
            issues.append(f"symlink file: {relative}")
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != expected[relative]:
            issues.append(f"hash mismatch: {relative}")

    for relative in sorted(actual & expected.keys()):
        if not relative.casefold().endswith((".html", ".htm")):
            continue
        html_path = bundle / relative
        if html_path.is_symlink() or bundle not in html_path.resolve().parents:
            continue
        collector = LinkCollector()
        try:
            collector.feed(html_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            issues.append(f"unreadable HTML: {relative}")
            continue
        for link in collector.links:
            try:
                parts = urlsplit(link)
            except ValueError:
                issues.append(f"invalid URL in {relative}: {link}")
                continue
            if parts.scheme or parts.netloc:
                issues.append(f"external URL in {relative}: {link}")
                continue
            decoded_path = unquote(parts.path)
            if not decoded_path:
                continue
            if "\x00" in decoded_path:
                issues.append(f"invalid link path in {relative}")
                continue
            windows_path = PureWindowsPath(decoded_path)
            link_path = PurePosixPath(decoded_path)
            if ("\\" in decoded_path or windows_path.is_absolute() or windows_path.drive
                    or link_path.is_absolute() or ".." in link_path.parts):
                issues.append(f"unsafe link in {relative}: {link}")
                continue
            target = (html_path.parent / Path(*link_path.parts)).resolve()
            if bundle not in target.parents:
                issues.append(f"unsafe link target in {relative}: {link}")
            elif not target.is_file():
                issues.append(f"missing link target in {relative}: {link}")

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle")
    arguments = parser.parse_args()
    issues = verify_bundle(arguments.bundle)
    if issues:
        print("FAIL")
        print("\n".join(issues))
        return 1
    print("PASS: manifest inventory and SHA-256 hashes match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
