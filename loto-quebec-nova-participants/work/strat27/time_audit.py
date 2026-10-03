from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ParsedTimestamp:
    source_text: str
    precision: str
    start_inclusive: datetime | None
    end_exclusive: datetime | None
    timezone_confidence: str


def parse_timestamp(source_text, source_timezone=None):
    if not isinstance(source_text, str):
        raise ValueError("timestamp must be text")
    if re.fullmatch(r"\d{2}/\d{2}/\d{2,4}", source_text):
        raise ValueError("ambiguous short date format")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", source_text):
        day = date.fromisoformat(source_text)
        return ParsedTimestamp(source_text, "day", datetime.combine(day, time.min),
                               datetime.combine(day + timedelta(days=1), time.min),
                               "date-only; timezone unspecified")

    timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}(?::\d{2}(?::\d{2}(?:\.\d{1,6})?)?)?(?:Z|[+-]\d{2}:\d{2})?"
    if re.fullmatch(timestamp_pattern, source_text) is None:
        raise ValueError("timestamp must use the supported ISO 8601 form")

    if "." in source_text:
        fraction = re.search(r"\.(\d+)", source_text).group(1)
        precision = "fractional-second"
        interval_width = timedelta(microseconds=10 ** (6 - len(fraction)))
    elif re.search(r"T\d{2}:\d{2}:\d{2}", source_text):
        precision = "second"
        interval_width = timedelta(seconds=1)
    elif re.search(r"T\d{2}:\d{2}", source_text):
        precision = "minute"
        interval_width = timedelta(minutes=1)
    else:
        precision = "hour"
        interval_width = timedelta(hours=1)

    normalized = source_text[:-1] + "+00:00" if source_text.endswith("Z") else source_text
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        if source_timezone is None:
            raise ValueError("timezone missing; provide a source timezone or retain as unresolved")
        zone = ZoneInfo(source_timezone)
        first = parsed.replace(tzinfo=zone, fold=0)
        second = parsed.replace(tzinfo=zone, fold=1)
        first_valid = first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == parsed
        second_valid = second.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == parsed
        if first_valid and second_valid and first.utcoffset() != second.utcoffset():
            return ParsedTimestamp(source_text, precision, None, None,
                                   f"ambiguous local time in {source_timezone}; exact offset unresolved")
        if not first_valid and not second_valid:
            return ParsedTimestamp(source_text, precision, None, None,
                                   f"nonexistent local time in {source_timezone}; exact time unresolved")
        parsed = first if first_valid else second
        timezone_confidence = f"localized using {source_timezone}"
    else:
        timezone_confidence = "explicit offset in source"

    interval_start_utc = parsed.astimezone(timezone.utc)
    interval_end_utc = interval_start_utc + interval_width
    return ParsedTimestamp(source_text, precision, interval_start_utc,
                           interval_end_utc, timezone_confidence)
