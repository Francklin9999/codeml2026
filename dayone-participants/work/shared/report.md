# DayOne evaluation foundation audit — 2026-10-03

A lower-cost subagent implemented a provisional Pydantic clinical schema and field-level evaluator. The parent audited the source and independently ran ten focused tests; all pass.

Audit fixes include duplicate page/field rejection, extra prediction page accounting, identifier-like keys across all predictions, strict numeric and unit comparisons, package/script imports, supported breakdown validation, nonempty ground truth, future two-digit date handling, tolerance boundary rounding and valid confidence-bin counts. Schema fields must match their page type; opaque patient code format is checked.

The metrics cover missing predictions, field and status accuracy, status confusion, hallucinated values for NON_FOURNI, extra fields/pages, potential identifier leaks, and confidence calibration. Breakdowns support page type, field type, language and severity when annotations supply those labels.

No reviewed specimen zones, eighty-page ground truth, checkbox extraction, phone-photo labels or OCR implementation are included. The provisional field inventory is not an enforced clinical ontology. Personal data embedded in otherwise allowed free-text values is not detected by these key-based checks. Strategy 1 remains IN PROGRESS.
