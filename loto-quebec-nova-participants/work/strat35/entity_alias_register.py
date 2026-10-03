def _normalize(alias):
    return " ".join(alias.split()).casefold()


def resolve_alias(query, register):
    if not isinstance(query, str) or not query.strip():
        return {"status": "invalid", "candidates": []}
    if not isinstance(register, list):
        return {"status": "invalid-register", "candidates": []}

    normalized_query = _normalize(query)
    reviewed_matches = set()
    review_needed = False
    for entity in register:
        if not isinstance(entity, dict):
            continue
        entity_id = entity.get("entity_id")
        preferred_label = entity.get("preferred_label")
        aliases = entity.get("aliases")
        if (not isinstance(entity_id, str) or not entity_id.strip()
                or not isinstance(preferred_label, str) or not preferred_label.strip()
                or not isinstance(aliases, list)):
            continue
        for alias in aliases:
            if not isinstance(alias, dict) or not isinstance(alias.get("text"), str):
                continue
            if _normalize(alias["text"]) != normalized_query:
                continue
            if (alias.get("reviewed") is True
                    and isinstance(alias.get("locator"), str) and alias["locator"].strip()
                    and isinstance(alias.get("reviewer"), str) and alias["reviewer"].strip()
                    and alias.get("confidence") == "high"):
                reviewed_matches.add((entity_id, preferred_label))
            else:
                review_needed = True

    candidates = [
        {"entity_id": entity_id, "preferred_label": preferred_label}
        for entity_id, preferred_label in sorted(reviewed_matches)
    ]
    if len(candidates) > 1:
        return {"status": "ambiguous", "candidates": candidates}
    if review_needed:
        return {"status": "review-required", "candidates": candidates}
    if candidates:
        return {"status": "resolved", "candidates": candidates}
    return {"status": "unmatched", "candidates": []}
