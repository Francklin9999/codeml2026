#!/usr/bin/env python3
"""Build the autonomous NOVA delivery into dist/."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.events import build_baseline, freeze_baseline, replay_events
from nova.extraction import extract_corpus
from nova.validation import load_json, require_valid_data


def read_locators(path: Path) -> dict[str, dict]:
    return {
        item["id"]: item
        for item in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def evidence_link(locator: str, locators: dict[str, dict]) -> str | None:
    item = locators.get(locator)
    if not item:
        return None
    return f"{item['evidence_file']}#{item['anchor']}"


def event_files(directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    return [load_json(path) for path in sorted(directory.glob("*.json"))]


def prepare_payload(data_dir: Path, extracted: Path, freeze: bool) -> dict:
    require_valid_data(data_dir, extracted)
    locators = read_locators(extracted / "locators.jsonl")
    facts = load_json(data_dir / "facts.json")
    answers = load_json(data_dir / "answers.json")
    sources = load_json(data_dir / "sources.json")

    def source_ref(file: str, locator: str, label: str | None = None) -> dict:
        return {
            "file": file,
            "locator": locator,
            "label": label or f"{file} · {locator}",
            "evidenceHref": evidence_link(locator, locators),
        }

    enriched_facts = []
    for fact in facts:
        item = dict(fact)
        item["evidence"] = [
            source_ref(fact["source_file"], fact["locator"])
        ]
        enriched_facts.append(item)

    enriched_answers = {}
    for question_id, answer in answers.items():
        item = dict(answer)
        item["id"] = question_id
        item["sources"] = [
            {
                **source,
                "evidenceHref": evidence_link(source.get("locator", ""), locators),
            }
            for source in answer.get("sources", [])
        ]
        enriched_answers[question_id] = item

    enriched_sources = []
    for source in sources:
        item = dict(source)
        item["file"] = source.get("path")
        item["class"] = source.get("classification")
        item["info_as_of"] = source.get("information_date")
        item["notes"] = source.get("classification_reason")
        item["evidenceHref"] = source.get("evidence_path")
        enriched_sources.append(item)

    baseline_path = data_dir / "baseline.json"
    if freeze:
        freeze_baseline(facts, baseline_path)
    baseline = load_json(baseline_path) if baseline_path.exists() else build_baseline(facts)
    updated_state, diffs = replay_events(baseline, event_files(data_dir / "events"))

    def registry(name: str) -> list:
        items = load_json(data_dir / f"{name}.json", [])
        enriched = []
        for original in items:
            item = dict(original)
            refs = item.get("fact_ids", [])
            item["evidence"] = [
                enriched_facts[[fact["id"] for fact in enriched_facts].index(ref)]["evidence"][0]
                for ref in refs
                if ref in {fact["id"] for fact in enriched_facts}
            ]
            enriched.append(item)
        return enriched

    return {
        "meta": {
            "project": "NOVA",
            "asOf": baseline["as_of"],
            "tools": ["Python", "HTML/CSS/JavaScript", "assistance IA déclarée"],
            "manualSteps": [
                "Validation humaine des citations et de leur autorité.",
                "Lecture visuelle des captures et tableaux dont l'ordre extrait est ambigu.",
            ],
            "baselineSha256": baseline.get("content_sha256"),
        },
        "brief": load_json(data_dir / "brief.json", {}),
        "facts": enriched_facts,
        "timeline": enriched_facts,
        "decisions": [
            item for item in enriched_facts
            if item.get("type") in {"proposal", "decision", "delivery", "validation"}
        ],
        "answers": enriched_answers,
        "actions": registry("actions"),
        "contradictions": registry("contradictions"),
        "risks": registry("risks"),
        "unknowns": registry("unknowns"),
        "sources": enriched_sources,
        "versions": {
            "baseline": baseline,
            "current": updated_state,
            "changes": diffs,
        },
        "diff": diffs,
    }


def safe_clean(directory: Path) -> None:
    resolved = directory.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name != "dist":
        raise ValueError(f"Refus de supprimer un chemin inattendu: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def build(args: argparse.Namespace) -> dict:
    extracted = ROOT / "work" / "_local"
    if args.extract or not (extracted / "inventory.json").exists():
        extract_corpus(ROOT / "NOVA_ETUDIANTS.zip", extracted, ROOT / "data" / "sources.json")
    payload = prepare_payload(ROOT / "data", extracted, args.freeze_baseline)
    destination = ROOT / "dist"
    safe_clean(destination)
    shutil.copytree(ROOT / "app", destination)
    shutil.copytree(extracted / "corpus", destination / "corpus")
    shutil.copytree(extracted / "evidence", destination / "evidence")
    data_js = "window.NOVA_DATA = " + json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + ";\n"
    (destination / "nova-data.js").write_text(data_js, encoding="utf-8", newline="\n")
    report = {
        "destination": str(destination),
        "facts": len(payload["facts"]),
        "sources": len(payload["sources"]),
        "events": len(payload["diff"]),
        "baseline_sha256": payload["meta"]["baselineSha256"],
    }
    (destination / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true", help="Reconstruire l'extraction locale")
    parser.add_argument(
        "--freeze-baseline",
        action="store_true",
        help="Créer ou vérifier data/baseline.json et son SHA-256",
    )
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Construction impossible: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
