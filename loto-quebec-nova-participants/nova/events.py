"""Immutable baseline and guarded live-event handling for NOVA."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


BASELINE_AS_OF = "2026-09-30T09:00:00-04:00"
VALIDATING_AUTHORITIES = {
    "accountable_owner_validation",
    "committee_decision",
    "pm_formal",
}
DECIDING_AUTHORITIES = {"committee_decision", "pm_formal"}
NON_MUTATING_KINDS = {"proposal", "unconfirmed", "observation"}


class EventError(ValueError):
    """Raised when a live event violates a project-memory guardrail."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise EventError(f"{field} doit être une date ISO 8601: {value!r}") from exc
    if parsed.tzinfo is None:
        raise EventError(f"{field} doit inclure un fuseau horaire")
    return parsed


def build_baseline(facts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build the frozen state using current, non-proposal facts only."""

    fact_list = list(facts)
    current: dict[str, dict[str, Any]] = {}
    history: dict[str, list[str]] = {}
    proposals: dict[str, list[str]] = {}

    for fact in fact_list:
        subject = fact.get("subject")
        fact_id = fact.get("id")
        if not subject or not fact_id:
            raise EventError("Chaque fait doit avoir id et subject")
        history.setdefault(subject, []).append(fact_id)
        if fact.get("type") == "proposal" or fact.get("status") == "proposal-only":
            proposals.setdefault(subject, []).append(fact_id)
            continue
        if fact.get("status") != "current":
            continue
        previous = current.get(subject)
        if previous is None:
            current[subject] = fact
            continue
        previous_date = previous.get("info_as_of") or previous.get("date") or ""
        candidate_date = fact.get("info_as_of") or fact.get("date") or ""
        previous_rank = int(previous.get("authority_rank", 0))
        candidate_rank = int(fact.get("authority_rank", 0))
        if (candidate_rank, candidate_date, fact_id) > (
            previous_rank,
            previous_date,
            previous["id"],
        ):
            current[subject] = fact

    compact_current = {
        subject: {
            "fact_id": fact["id"],
            "statement": fact.get("statement", ""),
            "status": fact.get("lifecycle_status", fact.get("status", "current")),
            "authority": fact.get("authority", "unknown"),
            "date": fact.get("date"),
            "source_file": fact.get("source_file"),
            "locator": fact.get("locator"),
        }
        for subject, fact in sorted(current.items())
    }
    baseline = {
        "schema_version": 1,
        "project": "NOVA",
        "as_of": BASELINE_AS_OF,
        "current": compact_current,
        "history": {key: sorted(value) for key, value in sorted(history.items())},
        "proposals": {key: sorted(value) for key, value in sorted(proposals.items())},
        "event_log": [],
    }
    baseline["content_sha256"] = sha256_json(baseline)
    return baseline


def freeze_baseline(facts: Iterable[dict[str, Any]], destination: Path) -> str:
    """Create a baseline once, or verify the existing frozen file byte-for-byte."""

    baseline = build_baseline(facts)
    encoded = json.dumps(baseline, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    hash_path = destination.with_suffix(destination.suffix + ".sha256")

    if destination.exists():
        existing = destination.read_bytes()
        existing_digest = hashlib.sha256(existing).hexdigest()
        recorded = hash_path.read_text(encoding="utf-8").strip() if hash_path.exists() else ""
        if existing_digest != recorded:
            raise EventError("La baseline existante ne correspond plus à son SHA-256")
        if existing != encoded.encode("utf-8"):
            raise EventError("Les faits courants diffèrent de la baseline gelée")
        return existing_digest

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(encoded, encoding="utf-8", newline="\n")
    hash_path.write_text(digest + "\n", encoding="utf-8", newline="\n")
    return digest


def _validate_event(event: dict[str, Any], state: dict[str, Any]) -> None:
    required = {
        "event_id",
        "record_time",
        "valid_time",
        "subject",
        "kind",
        "statement",
        "actor",
        "authority",
        "source",
    }
    missing = sorted(required - event.keys())
    if missing:
        raise EventError(f"Événement incomplet: {', '.join(missing)}")
    record_time = _parse_timestamp(event["record_time"], "record_time")
    _parse_timestamp(event["valid_time"], "valid_time")
    if record_time <= _parse_timestamp(BASELINE_AS_OF, "baseline.as_of"):
        raise EventError("Un événement live doit être appris après le baseline")
    if any(item.get("event_id") == event["event_id"] for item in state.get("event_log", [])):
        raise EventError(f"event_id déjà utilisé: {event['event_id']}")

    kind = event["kind"]
    authority = event["authority"]
    if kind in {"validation", "accepted", "closed"} and authority not in VALIDATING_AUTHORITIES:
        raise EventError("Une livraison fournisseur ne constitue pas une validation")
    if kind in {"decision", "approval"} and authority not in DECIDING_AUTHORITIES:
        raise EventError("Cette autorité ne peut pas approuver une décision de gouvernance")
    if event.get("affects_subjects"):
        forbidden = set(event["affects_subjects"]) - {event["subject"]}
        if forbidden:
            raise EventError("Un événement ne peut modifier silencieusement un autre sujet")


def apply_event(
    baseline: dict[str, Any], event: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply one event without mutating the baseline and return state plus explicit diff."""

    before_fingerprint = sha256_json(baseline)
    state = copy.deepcopy(baseline)
    _validate_event(event, state)
    subject = event["subject"]
    previous = copy.deepcopy(state.get("current", {}).get(subject))
    kind = event["kind"]
    mutates = kind not in NON_MUTATING_KINDS and not event.get("ambiguous", False)

    if mutates:
        state.setdefault("current", {})[subject] = {
            "event_id": event["event_id"],
            "statement": event["statement"],
            "status": event.get("new_status", kind.upper()),
            "authority": event["authority"],
            "date": event["valid_time"],
            "source": event["source"],
        }
    else:
        state.setdefault("proposals", {}).setdefault(subject, []).append(event["event_id"])

    state.setdefault("event_log", []).append(copy.deepcopy(event))
    current = state.get("current", {}).get(subject)
    affected_answers = sorted(set(event.get("affects_answers", [])))
    affected_actions = sorted(set(event.get("affects_actions", [])))
    unchanged = sorted(
        key for key in baseline.get("current", {}) if key != subject
    )
    diff = {
        "event_id": event["event_id"],
        "subject": subject,
        "kind": kind,
        "changed": mutates,
        "before": previous,
        "after": current if mutates else previous,
        "proposal_or_unconfirmed": None if mutates else event["statement"],
        "affected_answers": affected_answers,
        "affected_actions": affected_actions,
        "unchanged_subjects": unchanged,
        "explanation": (
            "L'état courant est modifié par une information autorisée."
            if mutates
            else "La décision antérieure reste en vigueur; l'information est conservée sans être appliquée."
        ),
        "baseline_sha256": baseline.get("content_sha256"),
    }
    if sha256_json(baseline) != before_fingerprint:
        raise AssertionError("La baseline a été modifiée en mémoire")
    return state, diff

