#!/usr/bin/env python3
"""Freeze NOVA's baseline, preview a live event, or append it safely."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova.events import EventError, apply_event, freeze_baseline, replay_events


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_frozen_baseline(path: Path) -> dict:
    if not path.exists():
        raise EventError("Baseline absente; exécutez d'abord la commande freeze")
    hash_path = path.with_suffix(path.suffix + ".sha256")
    expected = hash_path.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise EventError("Baseline modifiée: le SHA-256 ne correspond plus")
    return read_json(path)


def existing_events(directory: Path) -> list[dict]:
    return [read_json(path) for path in sorted(directory.glob("*.json"))]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("freeze", help="Créer ou vérifier la baseline")
    freeze.add_argument("--facts", type=Path, default=ROOT / "data" / "facts.json")
    freeze.add_argument(
        "--baseline", type=Path, default=ROOT / "data" / "baseline.json"
    )
    for name in ("preview", "append"):
        command = sub.add_parser(name, help=f"{name} un événement JSON")
        command.add_argument("event", type=Path)
        command.add_argument(
            "--baseline", type=Path, default=ROOT / "data" / "baseline.json"
        )
        command.add_argument(
            "--events", type=Path, default=ROOT / "data" / "events"
        )
        command.add_argument("--output", type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "freeze":
            digest = freeze_baseline(read_json(args.facts), args.baseline)
            print(json.dumps({"baseline": str(args.baseline), "sha256": digest}, ensure_ascii=False))
            return 0

        baseline = verify_frozen_baseline(args.baseline)
        state, diffs = replay_events(baseline, existing_events(args.events))
        candidate = read_json(args.event)
        next_state, diff = apply_event(state, candidate)
        payload = {"state": next_state, "diffs": [*diffs, diff]}
        rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8", newline="\n")
        else:
            print(rendered, end="")

        if args.command == "append":
            args.events.mkdir(parents=True, exist_ok=True)
            target = args.events / f"{candidate['event_id']}.json"
            if target.exists():
                raise EventError(f"L'événement existe déjà: {target.name}")
            target.write_text(
                json.dumps(candidate, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"Événement ajouté: {target}", file=sys.stderr)
        return 0
    except (EventError, KeyError, json.JSONDecodeError, OSError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
