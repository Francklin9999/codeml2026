"""Cross-file validation for the curated NOVA memory."""

from __future__ import annotations

import json
import re
import unicodedata
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


def _normalise_evidence(value: str) -> str:
    value = value.replace("**", "").replace("\u00a0", " ")
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def _quote_variants(value: str) -> set[str]:
    """Return reasonable quote forms for units that store timestamp metadata separately."""
    variants = {_normalise_evidence(value)}
    without_timestamp = re.sub(
        r"^\s*\d{1,2}\s+[A-Za-zÀ-ÿ.]+\s+\d{1,2}:\d{2}\s*[-–:]\s*",
        "",
        value,
    )
    variants.add(_normalise_evidence(without_timestamp))
    return {variant for variant in variants if variant}


def validate_evidence(data_dir: Path, extracted_root: Path) -> list[str]:
    """Ensure each curated quote, source and locator exists in extracted evidence."""

    errors: list[str] = []
    facts = load_json(data_dir / "facts.json", [])
    inventory = load_json(extracted_root / "inventory.json", {"sources": []})
    sources = {item["path"]: item for item in inventory.get("sources", [])}
    locators: dict[str, dict[str, Any]] = {}
    duplicate_locators: set[str] = set()
    locator_path = extracted_root / "locators.jsonl"
    if locator_path.exists():
        for line_number, line in enumerate(locator_path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                item = json.loads(line)
                locator_id = item.get("id")
                if not locator_id:
                    errors.append(f"locators.jsonl:{line_number}: id absent")
                    continue
                if locator_id in locators:
                    duplicate_locators.add(locator_id)
                    continue
                locators[locator_id] = item
        for locator_id in sorted(duplicate_locators):
            errors.append(f"locateur dupliqué {locator_id!r}")
    else:
        errors.append("locators.jsonl absent")

    for index, fact in enumerate(facts):
        fact_id = fact.get("id", f"facts[{index}]")
        source_file = fact.get("source_file")
        locator = fact.get("locator")
        quote = str(fact.get("quote", ""))
        source = sources.get(source_file)
        if source is None:
            errors.append(f"{fact_id}: source inconnue {source_file!r}")
            continue
        locator_record = locators.get(locator)
        if locator_record is None:
            errors.append(f"{fact_id}: locateur inconnu {locator!r}")
        text_path = extracted_root / source["text_path"]
        if not text_path.is_file():
            errors.append(f"{fact_id}: texte extrait absent {source['text_path']}")
            continue
        if locator_record is None:
            continue
        if locator_record.get("file") != source_file:
            errors.append(
                f"{fact_id}: le locateur {locator!r} appartient à "
                f"{locator_record.get('file')!r}, pas à {source_file!r}"
            )
            continue
        unit_text = _normalise_evidence(str(locator_record.get("text", "")))
        if not any(variant in unit_text for variant in _quote_variants(quote)):
            errors.append(f"{fact_id}: citation introuvable dans l'unité {locator!r}")
    return errors


def require_valid_data(data_dir: Path, extracted_root: Path | None = None) -> None:
    errors = validate_data(data_dir)
    if extracted_root is not None:
        errors.extend(validate_evidence(data_dir, extracted_root))
    if errors:
        raise ValidationFailure("\n".join(errors))
