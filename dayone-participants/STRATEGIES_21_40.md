# DayOne strategies 21–40

All 20 entries are **proposals, not implementations**. Current evidence and scope limits are summarized in [RESULTS_OVERVIEW.md](../RESULTS_OVERVIEW.md): schema/evaluator tests pass, but there are no reviewed ground-truth pages or working phone OCR results. Existing strategy implementations were checked against each proposal before assigning the nearest predecessor below.

| # | Proposal · priority | Dependencies | Nearest existing strategy and mechanism difference | Proposed first experiment |
|---|---|---|---|---|
| 21 | [Patient-grouped holdout and duplicate leakage audit](strat21.md) · P1 | 1, 4, 5 | 4 generates degraded samples; this freezes patient-group splits and checks cross-split duplicates. | Split the 80 pages by opaque patient group; audit all 44 duplicate pairs. |
| 22 | [Reviewer disagreement and adjudication queue](strat22.md) · P1 | 1; 21 optional | 1 builds zones/labels; this runs blind independent review and adjudicates annotation conflicts. | Double-label 160 stratified fields and audit 30 adjudications. |
| 23 | [Annotation instructions as executable test fixtures](strat23.md) · P2 | 1, evaluator | 7 checks cross-field plausibility; this tests transcription/status conventions without clinical rules. | Run 40 convention examples, then blind-classify a separate 40. |
| 24 | [Field-aware crop boundary diagnostics](strat24.md) · P2 | 1 zones, 2 registration | 2 extracts zonal crops; this detects and flags clipped field context before recognition. | Inject 0–8 px zone shifts on 80 fields; score clip detection and leakage. |
| 25 | [Document-set completeness manifest](strat25.md) · P2 | 1; 17 optional | 17 finds page order/duplicates; this tracks expected packet slots and unresolved omissions. | Test 30 packet scenarios including missing, duplicate, and uncertain pages. |
| 26 | [Privacy-safe error analytics](strat26.md) · P1 | 1 evaluator; 8 optional | 19 aggregates health records; this emits minimized model-quality events with a strict allowlist. | Inject forbidden data in 500 synthetic events and test suppression. |
| 27 | [Field-level data lineage and versioned transformations](strat27.md) · P2 | 1; 21 optional | 1 defines labels/schema; this records deterministic normalization and correction history for each field. | Replay 50 synthetic field histories and change one rule version. |
| 28 | [Review-time keyboard and correction ergonomics study](strat28.md) · P2 | 9; evaluator optional | 9 defines deterministic dialogue; this compares field-edit ergonomics across layouts. | Five internal reviewers complete randomized synthetic correction tasks. |
| 29 | [Capture-session clock and event ordering audit](strat29.md) · P2 | 8, 17 | 8 persists queue states; this validates causal ordering despite clock rollback and delayed sync. | Simulate 100 sessions with restart, retry, and clock changes. |
| 30 | [Handwriting-preserving image transform audit](strat30.md) · P2 | 2, 4 | 4 simulates photo degradation; this measures stroke damage caused by rectification/resampling. | Compare five transform options on 60 synthetic strokes and 40 reviewed crops. |
| 31 | [Per-field evidence packet export](strat31.md) · P2 | 9; 21 optional | 9 displays evidence crops in chat; this defines a validated portable evidence-packet contract. | Validate 60 synthetic packets and block 20 malformed ones. |
| 32 | [Schema migration and backward-compatibility gate](strat32.md) · P2 | 1 | 1 defines a provisional schema; this tests explicit migrations and rejects silent field loss. | Migrate 30 synthetic records across three draft versions. |
| 33 | [Field dependency map for review navigation](strat33.md) · P2 | 1, 9 | 7 validates clinical consistency; this displays layout relationships without inference. | Compare navigation time on 24 synthetic review tasks. |
| 34 | [Table-row association benchmark](strat34.md) · P2 | 1 zones, 2 registration | 2 performs extraction; this scores row/column binding separately from character recognition. | Generate 200 adversarial tables; reserve 40 reviewed crops as holdout. |
| 35 | [Status transition policy audit](strat35.md) · P1 | 1 | 6 maps confidence to status; this controls allowed human/system status transitions. | Enumerate status pairs and 20 scripted review actions. |
| 36 | [Offline language-pack and font coverage manifest](strat36.md) · P2 | 5; 15 optional | 5 synthesizes multilingual pages; this tests offline UI rendering and input direction. | Render 60 strings on two browser engines without network access. |
| 37 | [Retention and deletion lifecycle rehearsal](strat37.md) · P1 | 8, 10 | 10 masks identifiers; this checks synthetic records disappear across cache, store, and retries. | Delete 25 test records offline/online, restart, and retry sync. |
| 38 | [Deterministic extraction replay harness](strat38.md) · P2 | 1; local extractor | 6 calibrates confidence; this pins inputs/configuration and detects run-to-run output drift. | Replay 100 synthetic crops three times and after a dependency update. |
| 39 | [Manual fallback parity contract](strat39.md) · P2 | 9, 15 | 15 supports offline capture; this ensures manual and corrected records serialize identically. | Enter 40 synthetic fields through both paths and compare normalized output. |
| 40 | [Challenge-brief traceability matrix](strat40.md) · P3 | Brief, strategy set | Existing reports log strategy results; this maps every product claim to evidence and status. | Audit 20 requirements and 10 demo claims for traceability. |

## First picks

1. **21 — Leakage audit:** the dataset has ten patient groups and known duplicate renders; a split error could invalidate future OCR claims.
2. **22 — Independent annotation:** no reviewed labels exist, so measuring annotator disagreement is an early prerequisite to trusting model scores.
3. **26 — Privacy-safe analytics:** it addresses a documented evaluator blind spot (free-text personal data) through minimization and tests rather than unsupported detection claims.

## Evidence note

Measured implementation results are not repeated here; see [the integrated results overview](../RESULTS_OVERVIEW.md). No strategy in this index has been run. Personal or health data must not be sent to external services. Strategies 21–40 are independent proposals; priorities are planning judgments, not measured outcomes.
