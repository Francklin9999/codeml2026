# Shared schema and evaluator

`schema.py` defines `Page`, `ClinicalField`, and the six extraction statuses. It also lists provisional clinical field keys by page type; these have not yet been checked against page zones or specimen pages. The schema rejects identifier-like field keys (names, CIN, phone, address, and identifying profession); use an opaque random hexadecimal `patient_ref` (8–32 characters). This format check cannot prove that a code was randomly generated.

Run evaluation from the repository root with Python 3.10+ and Pydantic 2.x:

```powershell
.\.venv\Scripts\python.exe dayone-participants\work\shared\eval.py --pred dayone-participants\work\strat3\out --gt dayone-participants\work\shared\gt --output dayone-participants\work\_local\eval_run.json
```

Each JSON file can contain one page or a list of pages. A page has `page_type`, optional `patient_ref`, and `fields` as a list of objects (`key`, `value` or `normalized`, `status`, optional `confidence`, and optional `type`). Alternatively, `fields` may be a mapping from key to field object. Predictions are paired with ground truth by `(patient_ref, page_type)`; a missing page therefore counts as missing predictions. Results include overall and page-type field accuracy, status confusion, values predicted for `NON_FOURNI`, extra keys and identifier-like extra keys, and expected calibration error (ECE) with reliability bins.

Dates accept common French day/month formats and ISO. Numeric values use ±0.1 for weight, haemoglobin, and temperature; other numeric fields compare exactly. Blood pressure compares integer systolic/diastolic pairs, known aliases normalize for common enum values, and free text uses a 0.9 normalized similarity threshold. For reliable typing, include `type` on both ground-truth and prediction fields (`date`, `number`, `enum`, `text`, `blood_pressure`, etc.).

Focused tests: `.\.venv\Scripts\python.exe -m unittest discover -s dayone-participants\work\shared\tests -v`.

## Scope and limitations

The evaluator is an initial shared baseline. `--by` supports `page_type`, `field_type`, `lang`, and `severity`; dimensions without labels are reported as `unknown`. It does not create or infer ground truth. Add form-specific enum aliases and field types as validated annotations become available. Identifier detection flags identifier-like keys on every prediction page plus invalid patient-code formats; it does not inspect free-text values for embedded personal data. Numeric units must match; unit conversion is not implemented. Two-digit dates use Python's fixed 1969–2068 pivot, so prefer four-digit years in annotations.

Parent audit: ten tests pass after duplicate-page/key validation, strict numeric parsing, extra-page privacy checks, future-date handling and tolerance-boundary fixes. No specimen page annotations or real-photo ground truth were created.
