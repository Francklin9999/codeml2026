"""Field-level evaluation for DayOne extraction outputs; standard library only."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

try:
    from .schema import IDENTIFIER_KEY
except ImportError:
    from schema import IDENTIFIER_KEY

TOLERANCE = {"weight": 0.1, "haemoglobin": 0.1, "hemoglobin": 0.1, "temperature": 0.1}
ENUM_ALIASES = {
    "ras": "NORMAL", "normal": "NORMAL", "normale": "NORMAL", "normales": "NORMAL", "normale(s)": "NORMAL",
    "neg": "NEG", "negative": "NEG", "negatif": "NEG", "negativee": "NEG",
    "oui": "YES", "yes": "YES", "non": "NO", "no": "NO",
}
def _fields(obj: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields = obj.get("fields", [])
    if isinstance(fields, dict):
        keys = [str(key) for key in fields]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate field keys")
        return {str(key): (value if isinstance(value, dict) else {"value": value}) for key, value in fields.items()}
    result = {}
    for field in fields:
        if not isinstance(field, dict) or "key" not in field:
            raise ValueError("each field must be an object with a key")
        key = str(field["key"])
        if key in result:
            raise ValueError(f"duplicate field key: {key}")
        result[key] = field
    return result


def _status(field: dict[str, Any]) -> str:
    return str(field.get("status", "")).upper()


def _value(field: dict[str, Any]) -> Any:
    return field.get("normalized") if field.get("normalized") is not None else field.get("value")


def _text(value: Any) -> str:
    value = unicodedata.normalize("NFKD", str(value).strip().casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value)


def _date(value: Any) -> str | None:
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            parsed = dt.datetime.strptime(text, fmt).date()
            return parsed.isoformat()
        except ValueError:
            pass
    return None


def _number(value: Any) -> tuple[float, str] | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        return (number, "") if math.isfinite(number) else None
    text = str(value).strip().replace(",", ".")
    match = re.fullmatch(r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*([a-zA-Z°/]+)?", text)
    if not match:
        return None
    number = float(match.group(1))
    if not math.isfinite(number):
        return None
    unit_aliases = {"kgs": "kg", "grams": "g", "gram": "g", "c": "°c", "°c": "°c", "g/dl": "g/dl"}
    unit = match.group(2).lower() if match.group(2) else ""
    return number, unit_aliases.get(unit, unit)


def values_match(key: str, gold: dict[str, Any], pred: dict[str, Any]) -> bool:
    """Compare values using explicit metadata first, then conservative key inference."""
    expected, actual = _value(gold), _value(pred)
    if expected is None or actual is None:
        return expected is actual
    kind = str(gold.get("type", gold.get("field_type", pred.get("type", pred.get("field_type", ""))))).lower()
    key_lower = key.lower()
    if kind == "date" or key_lower.endswith((".date", ".ddr", ".edd", "_date", "appointment")):
        left, right = _date(expected), _date(actual)
        return left is not None and right is not None and left == right
    if kind in {"number", "number_unit", "numeric"} or any(term in key_lower for term in TOLERANCE):
        left, right = _number(expected), _number(actual)
        if left is None or right is None:
            return False
        if left[1] != right[1]:
            return False
        tolerance = next((tol for term, tol in TOLERANCE.items() if term in key_lower), 0.0)
        return abs(left[0] - right[0]) <= tolerance + (1e-9 if tolerance else 0)
    if kind in {"blood_pressure", "bp"} or "blood_pressure" in key_lower or key_lower.endswith(".ta"):
        nums_expected, nums_actual = re.findall(r"\d+", str(expected)), re.findall(r"\d+", str(actual))
        return len(nums_expected) == len(nums_actual) == 2 and nums_expected == nums_actual
    left_text, right_text = _text(expected), _text(actual)
    left_enum = re.sub(r"[^a-z0-9]", "", left_text)
    right_enum = re.sub(r"[^a-z0-9]", "", right_text)
    if left_text in ENUM_ALIASES or right_text in ENUM_ALIASES or kind in {"enum", "boolean"}:
        return ENUM_ALIASES.get(left_text, ENUM_ALIASES.get(left_enum, left_enum)) == ENUM_ALIASES.get(right_text, ENUM_ALIASES.get(right_enum, right_enum))
    if kind in {"text", "free_text"} or isinstance(expected, str) or isinstance(actual, str):
        return SequenceMatcher(None, left_text, right_text).ratio() >= 0.9
    return expected == actual


def _confusion(gold: str, pred: str, matrix: dict[str, dict[str, int]]) -> None:
    matrix.setdefault(gold, {})[pred] = matrix.setdefault(gold, {}).get(pred, 0) + 1


def evaluate(ground_truth: list[dict[str, Any]], predictions: list[dict[str, Any]], bins: int = 10,
             breakdown_by: tuple[str, ...] = ("page_type",)) -> dict[str, Any]:
    """Return field/status accuracy, extra-key/privacy, hallucination and ECE metrics."""
    if isinstance(bins, bool) or not isinstance(bins, int) or bins <= 0:
        raise ValueError("calibration bins must be a positive integer")
    pred_by_ref = {}
    for page in predictions:
        ref = str(page.get("patient_ref", "")) + ":" + str(page.get("page_type", ""))
        if ref in pred_by_ref:
            raise ValueError("duplicate prediction page identity")
        pred_by_ref[ref] = page
    gt_by_ref = {}
    for page in ground_truth:
        ref = str(page.get("patient_ref", "")) + ":" + str(page.get("page_type", ""))
        if ref in gt_by_ref:
            raise ValueError("duplicate ground-truth page identity")
        gt_by_ref[ref] = page
    if not gt_by_ref:
        raise ValueError("ground-truth set is empty")
    field_total = field_correct = status_correct = status_total = 0
    confusion: dict[str, dict[str, int]] = {}
    extras: list[dict[str, Any]] = []
    extra_pages = 0
    invalid_patient_refs = sum(
        bool(page.get("patient_ref") and not re.fullmatch(r"[A-Fa-f0-9]{8,32}", str(page["patient_ref"])))
        for page in predictions
    )
    hallucinated = nonprovided = 0
    calibration: list[tuple[float, bool]] = []
    breakdown: dict[str, dict[str, dict[str, int]]] = {name: {} for name in breakdown_by}

    for gt_page in ground_truth:
        ref = str(gt_page.get("patient_ref", "")) + ":" + str(gt_page.get("page_type", ""))
        pred_page = pred_by_ref.get(ref, {})
        gt_fields, pred_fields = _fields(gt_page), _fields(pred_page)
        if any(IDENTIFIER_KEY.search(key) for key in gt_fields):
            raise ValueError("ground-truth contains an identifier-like field key")
        for key in pred_fields.keys() - gt_fields.keys():
            extras.append({"key": key, "identifier_leak": bool(IDENTIFIER_KEY.search(key))})
        for key, gold in gt_fields.items():
            pred = pred_fields.get(key)
            field_total += 1
            gt_status, pred_status = _status(gold), _status(pred) if pred else "MISSING"
            status_total += 1
            status_correct += gt_status == pred_status
            _confusion(gt_status or "MISSING", pred_status or "MISSING", confusion)
            has_value = pred is not None and _value(pred) is not None
            if gt_status == "NON_FOURNI" and has_value:
                hallucinated += 1
            if gt_status == "NON_FOURNI":
                nonprovided += 1
            correct = bool(pred and gt_status == pred_status and values_match(key, gold, pred))
            field_correct += correct
            labels = {
                "page_type": str(gt_page.get("page_type", "unknown")),
                "field_type": str(gold.get("type", gold.get("field_type", "unknown"))),
                "lang": str(gold.get("lang", "unknown")),
                "severity": str(gold.get("severity", "unknown")),
            }
            for dimension in breakdown_by:
                group = labels[dimension]
                metric = breakdown[dimension].setdefault(group, {"total": 0, "correct": 0})
                metric["total"] += 1
                metric["correct"] += correct
            if pred and pred.get("confidence") is not None:
                try:
                    confidence = float(pred["confidence"])
                    if 0.0 <= confidence <= 1.0:
                        calibration.append((confidence, correct))
                except (TypeError, ValueError):
                    pass

    for ref, pred_page in pred_by_ref.items():
        if ref not in gt_by_ref:
            extra_pages += 1
            try:
                _fields(pred_page)
            except ValueError:
                raise
            for key in _fields(pred_page):
                extras.append({"key": key, "identifier_leak": bool(IDENTIFIER_KEY.search(key)), "extra_page": True})

    ece = 0.0
    reliability = []
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        items = [(confidence, correct) for confidence, correct in calibration
                 if low <= confidence < high or (index == bins - 1 and confidence == 1.0)]
        if items:
            mean_conf = sum(confidence_value for confidence_value, _ in items) / len(items)
            accuracy = sum(ok for _, ok in items) / len(items)
            ece += len(items) / max(len(calibration), 1) * abs(mean_conf - accuracy)
            reliability.append({"low": low, "high": high, "count": len(items), "confidence": mean_conf, "accuracy": accuracy})

    return {
        "fields": {"total": field_total, "correct": field_correct, "accuracy": field_correct / field_total if field_total else None},
        "status": {"total": status_total, "correct": status_correct, "accuracy": status_correct / status_total if status_total else None, "confusion": confusion},
        "breakdowns": {dimension: {name: {**metric, "accuracy": metric["correct"] / metric["total"]}
                                    for name, metric in groups.items()} for dimension, groups in breakdown.items()},
        "by_page_type": {name: {**metric, "accuracy": metric["correct"] / metric["total"]}
                         for name, metric in breakdown.get("page_type", {}).items()},
        "hallucinations": {"count": hallucinated, "non_furnished_fields": nonprovided, "rate": hallucinated / nonprovided if nonprovided else None},
        "extras": extras,
        "extra_prediction_pages": extra_pages,
        "identifier_leaks": sum(bool(IDENTIFIER_KEY.search(key)) for page in predictions for key in _fields(page)) + invalid_patient_refs,
        "invalid_patient_refs": invalid_patient_refs,
        "calibration": {"count": len(calibration), "ece": ece if calibration else None, "reliability_bins": reliability},
    }


def _read_pages(folder: Path) -> list[dict[str, Any]]:
    pages = []
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        pages.extend(data if isinstance(data, list) else [data])
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pred", type=Path, required=True)
    parser.add_argument("--gt", type=Path, required=True)
    parser.add_argument("--by", default="page_type", help="Accepted breakdown: page_type")
    parser.add_argument("--output", type=Path, help="Optional JSON result path")
    args = parser.parse_args()
    dimensions = tuple(part.strip() for part in args.by.split(",") if part.strip())
    unsupported = set(dimensions) - {"page_type", "field_type", "lang", "severity"}
    if unsupported:
        parser.error("unsupported breakdown dimension(s): " + ", ".join(sorted(unsupported)))
    result = evaluate(_read_pages(args.gt), _read_pages(args.pred), breakdown_by=dimensions)
    print("| Metric | Result |\n|---|---:|")
    print(f"| Field accuracy | {result['fields']['accuracy']} ({result['fields']['correct']}/{result['fields']['total']}) |")
    print(f"| Status accuracy | {result['status']['accuracy']} ({result['status']['correct']}/{result['status']['total']}) |")
    print(f"| Hallucination rate | {result['hallucinations']['rate']} ({result['hallucinations']['count']}/{result['hallucinations']['non_furnished_fields']}) |")
    print(f"| Identifier leaks | {result['identifier_leaks']} |")
    print(f"| ECE | {result['calibration']['ece']} |")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
