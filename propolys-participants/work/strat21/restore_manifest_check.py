from datetime import datetime


REQUIRED_FIELDS = {
    "service_id",
    "backup_job_id",
    "restore_started_at",
    "restore_completed_at",
    "integrity_status",
    "dependency_status",
    "owner_signoff",
    "evidence_source",
}


def check_restore_record(record):
    if not isinstance(record, dict):
        return ["record must be an object"]
    missing = sorted(field for field in REQUIRED_FIELDS if field not in record)
    invalid = sorted(field for field in REQUIRED_FIELDS
                     if field in record and (not isinstance(record[field], str)
                                             or not record[field].strip()))
    issues = []
    if missing:
        issues.append(f"missing fields: {', '.join(missing)}")
    if invalid:
        issues.append(f"invalid fields: {', '.join(invalid)}")
    integrity_status = record.get("integrity_status")
    if isinstance(integrity_status, str) and integrity_status.strip().casefold() == "verified":
        evidence = record.get("integrity_evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            issues.append("verified integrity lacks supporting evidence")
    owner_signoff = record.get("owner_signoff")
    if isinstance(owner_signoff, str) and owner_signoff.strip().casefold() in {"yes", "signed"}:
        owner_id = record.get("owner_id")
        if not isinstance(owner_id, str) or not owner_id.strip():
            issues.append("owner sign-off lacks owner identity")

    started_text = record.get("restore_started_at")
    completed_text = record.get("restore_completed_at")
    if isinstance(started_text, str) and isinstance(completed_text, str):
        try:
            start = datetime.fromisoformat(started_text.replace("Z", "+00:00"))
            completed = datetime.fromisoformat(completed_text.replace("Z", "+00:00"))
        except ValueError:
            issues.append("restore times must be ISO 8601 timestamps")
        else:
            if start.tzinfo is None or completed.tzinfo is None:
                issues.append("restore times require explicit timezone offsets")
            elif completed < start:
                issues.append("restore completion precedes start")
    return issues
