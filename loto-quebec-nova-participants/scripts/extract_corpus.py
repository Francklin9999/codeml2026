#!/usr/bin/env python3
"""Extract NOVA_ETUDIANTS.zip into reproducible local evidence artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nova.extraction import extract_corpus  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, default=REPO_ROOT / "NOVA_ETUDIANTS.zip")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "work" / "_local")
    parser.add_argument("--sources", type=Path, default=REPO_ROOT / "data" / "sources.json")
    args = parser.parse_args()
    try:
        report = extract_corpus(args.zip, args.output, args.sources)
    except Exception as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in ("source_count", "locator_count", "class_counts", "warnings")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

