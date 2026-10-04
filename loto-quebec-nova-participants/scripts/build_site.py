#!/usr/bin/env python3
"""Build the autonomous NOVA delivery into dist/."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.events import build_baseline, freeze_baseline, replay_events, sha256_json
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


def extraction_is_current(extracted: Path, zip_path: Path) -> bool:
    inventory_path = extracted / "inventory.json"
    locator_path = extracted / "locators.jsonl"
    if not inventory_path.is_file() or not locator_path.is_file():
        return False
    inventory = load_json(inventory_path, {})
    if inventory.get("zip_sha256") != hashlib.sha256(zip_path.read_bytes()).hexdigest():
        return False
    sources = inventory.get("sources", [])
    if len(sources) != 64:
        return False
    return all(
        (extracted / "corpus" / source["path"]).is_file()
        and (extracted / source["text_path"]).is_file()
        and (extracted / source["evidence_path"]).is_file()
        for source in sources
    )


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
    fact_by_id = {fact["id"]: fact for fact in enriched_facts}

    def references(fact_ids: list[str]) -> list[dict]:
        return [fact_by_id[fact_id]["evidence"][0] for fact_id in fact_ids if fact_id in fact_by_id]

    enriched_answers = {}
    for question_id, answer in answers.items():
        item = dict(answer)
        item["id"] = question_id
        # fact_ids are canonical; editorial source labels may span several locators.
        item["sources"] = references(answer.get("fact_ids", []))
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
    live_events = event_files(data_dir / "events")
    updated_state, diffs = replay_events(baseline, live_events)
    live_by_id = {event["event_id"]: event for event in live_events}

    def registry(name: str) -> list:
        items = load_json(data_dir / f"{name}.json", [])
        enriched = []
        for original in items:
            item = dict(original)
            refs = item.get("fact_ids", [])
            item["evidence"] = references(refs)
            updates = [
                event for event in live_events
                if item.get("id") in event.get("affects_actions", [])
            ] if name == "actions" else []
            if updates:
                item["eventUpdates"] = updates
                for event in updates:
                    new_status = event.get("action_updates", {}).get(item.get("id"))
                    if new_status:
                        item["status"] = new_status
            enriched.append(item)
        return enriched

    brief_raw = load_json(data_dir / "brief.json", {})
    brief_sections = {item.get("id"): item for item in brief_raw.get("sections", [])}

    def brief_item(section_id: str) -> dict | None:
        section = brief_sections.get(section_id)
        if not section:
            return None
        return {
            "text": section.get("summary", ""),
            # Keep the strict one-page brief readable; detailed views retain all proofs.
            "evidence": references(section.get("fact_ids", []))[:2],
        }

    brief = {
        "owner": brief_item("responsable"),
        "dateConditions": brief_item("date_conditions"),
        "scope": brief_item("portee"),
        "budget": brief_item("budget_factures"),
        "priorities": brief_item("priorites"),
        "uncertainties": brief_raw.get("caveats", []),
        "status": brief_raw.get("status"),
        "go_live_conditions": brief_raw.get("go_live_conditions", []),
        "eventUpdates": live_events,
    }

    if live_events:
        brief["status"] = (
            f"{brief.get('status', '')} Mise à jour live: "
            + " ".join(event["statement"] for event in live_events)
        ).strip()
        condition_subjects = {"SEC-210": 1, "ACC-303": 2, "OPS-601": 3}
        for condition in brief["go_live_conditions"]:
            for event in live_events:
                if condition.get("number") == condition_subjects.get(event.get("subject")):
                    condition["current_state"] = event["statement"]
                    condition["event_id"] = event["event_id"]
                    condition["status"] = event.get("new_status", event["kind"])

    display_diffs = []
    for diff in diffs:
        event = live_by_id.get(diff.get("event_id"), {})
        before = (diff.get("before") or {}).get("statement", "aucun état antérieur")
        after = (diff.get("after") or {}).get("statement", before)
        if not diff.get("changed"):
            after = diff.get("proposal_or_unconfirmed") or after
        display_diffs.append({
            **diff,
            "id": diff.get("event_id"),
            "title": f"{diff.get('subject')}: {diff.get('kind')}",
            "description": f"Avant: {before} Après: {after} {diff.get('explanation', '')}",
            "actor": event.get("actor"),
            "authority": event.get("authority"),
            "record_time": event.get("record_time"),
            "valid_time": event.get("valid_time"),
            "source": event.get("source"),
        })

    timeline_events = [
        {
            "id": event["event_id"],
            "date": event["valid_time"],
            "type": event["kind"],
            "status": event.get("new_status", "live"),
            "statement": event["statement"],
            "actor": event["actor"],
            "description": f"Événement appris le {event['record_time']}. Source: {event['source']}",
            "event": True,
        }
        for event in live_events
    ]

    for answer in enriched_answers.values():
        updates = [
            event for event in live_events
            if answer["id"] in event.get("affects_answers", [])
        ]
        if updates:
            answer["eventUpdates"] = updates
            answer["nuance"] = [
                *answer.get("nuance", []),
                *[f"Mise à jour live {event['event_id']}: {event['statement']}" for event in updates],
            ]

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
        "brief": brief,
        "facts": enriched_facts,
        "timeline": [*enriched_facts, *timeline_events],
        "decisions": [
            item for item in enriched_facts
            if item.get("type") in {"proposal", "decision", "delivery", "validation"}
        ] + [item for item in timeline_events if item.get("type") in {"proposal", "decision", "approval", "delivery", "validation", "accepted", "closed"}],
        "answers": enriched_answers,
        "actions": registry("actions"),
        "contradictions": registry("contradictions"),
        "risks": registry("risks"),
        "unknowns": registry("unknowns"),
        "sources": enriched_sources,
        "versions": {
            "baseline": {
                **baseline,
                "label": "Baseline gelée",
                "date": baseline.get("as_of"),
                "hash": sha256_json(updated_state),
            },
            "current": {
                **updated_state,
                "label": "État actualisé" if diffs else "Identique à la baseline",
                "date": (updated_state.get("event_log") or [{}])[-1].get("record_time", baseline.get("as_of")),
                "hash": baseline.get("content_sha256"),
            },
            "changes": display_diffs,
            "unchanged": diffs[-1].get("unchanged_subjects", []) if diffs else [],
        },
        "diff": display_diffs,
    }


def safe_clean(directory: Path) -> None:
    resolved = directory.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name not in {"dist", "dist.next", "dist.previous"}:
        raise ValueError(f"Refus de supprimer un chemin inattendu: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def build(args: argparse.Namespace) -> dict:
    extracted = ROOT / "work" / "_local"
    zip_path = ROOT / "NOVA_ETUDIANTS.zip"
    if args.extract or not extraction_is_current(extracted, zip_path):
        extract_corpus(ROOT / "NOVA_ETUDIANTS.zip", extracted, ROOT / "data" / "sources.json")
    payload = prepare_payload(ROOT / "data", extracted, args.freeze_baseline)
    destination = ROOT / "dist"
    staging = ROOT / "dist.next"
    previous = ROOT / "dist.previous"
    safe_clean(staging)
    safe_clean(previous)
    shutil.copytree(ROOT / "app", staging)
    shutil.copytree(extracted / "corpus", staging / "corpus")
    shutil.copytree(extracted / "evidence", staging / "evidence")
    data_js = "window.NOVA_DATA = " + json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + ";\n"
    (staging / "nova-data.js").write_text(data_js, encoding="utf-8", newline="\n")
    report = {
        "destination": "dist",
        "facts": len(payload["facts"]),
        "sources": len(payload["sources"]),
        "events": len(payload["diff"]),
        "baseline_sha256": payload["meta"]["baselineSha256"],
    }
    (staging / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    required = [staging / "index.html", staging / "nova-data.js", staging / "assets" / "app.js"]
    if not all(path.is_file() for path in required):
        raise RuntimeError("Livraison temporaire incomplète")
    if destination.exists():
        destination.rename(previous)
    try:
        staging.rename(destination)
    except Exception:
        if previous.exists() and not destination.exists():
            previous.rename(destination)
        raise
    safe_clean(previous)
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
