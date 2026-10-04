"""Cross-file validation for the curated NOVA memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ValidationFailure(ValueError):
    pass


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_data(data_dir: Path) -> list[str]:
    errors: list[str] = []
    facts = load_json(data_dir / "facts.json", [])
    answers = load_json(data_dir / "answers.json", {})
    ids: set[str] = set()
    required_fact = {
        "id",
        "subject",
        "type",
        "statement",
        "status",
        "source_file",
        "locator",
        "quote",
        "authority",
    }
    for index, fact in enumerate(facts):
        missing = required_fact - fact.keys()
        if missing:
            errors.append(f"facts[{index}] champs manquants: {sorted(missing)}")
        fact_id = fact.get("id")
        if fact_id in ids:
            errors.append(f"Identifiant de fait dupliqué: {fact_id}")
        if fact_id:
            ids.add(fact_id)
        if not str(fact.get("quote", "")).strip():
            errors.append(f"{fact_id or index}: citation vide")
    expected_questions = {f"Q{i:02d}" for i in range(1, 11)}
    missing_questions = expected_questions - answers.keys()
    if missing_questions:
        errors.append(f"Questions absentes: {sorted(missing_questions)}")
    for question_id, answer in answers.items():
        refs = answer.get("fact_ids", [])
        unknown = sorted(set(refs) - ids)
        if unknown:
            errors.append(f"{question_id}: faits inconnus {unknown}")
        if not answer.get("sources"):
            errors.append(f"{question_id}: aucune source")

    for filename in ("actions.json", "contradictions.json", "risks.json", "unknowns.json"):
        for index, item in enumerate(load_json(data_dir / filename, [])):
            refs = item.get("fact_ids", [])
            unknown = sorted(set(refs) - ids)
            if unknown:
                errors.append(f"{filename}[{index}]: faits inconnus {unknown}")
    return errors


def require_valid_data(data_dir: Path) -> None:
    errors = validate_data(data_dir)
    if errors:
        raise ValidationFailure("\n".join(errors))

