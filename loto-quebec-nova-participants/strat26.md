# NOVA · Strategy 26: Evidence packet export and offline integrity check

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (demo reliability) |
| **Effort** | 2–3 h |
| **Depends on** | final deliverable and source copies |
| **Rubric lines** | jury use; evidence access |
| **Work folder** | work/strat26/ |

## 1. Context and evidence

The rubric requires a no-paid-subscription deliverable, while strategies 1 and 7 target offline HTML and exact evidence links. Existing extraction and ledger work is incomplete. Packaging errors or broken relative paths could make otherwise accurate evidence inaccessible during the jury demonstration.

## 2. Idea and novelty

Create a deterministic export bundle with a SHA-256 manifest and a verifier that opens every internal link and checks every cited source exists. This differs from strategy 7's evidence-viewer design and strategy 24's source-quality review: it verifies the packaged artifact survives copying and offline opening.

## 3. Rubric

The jury receives a dependable, inspectable evidence bundle that works without network access or credentials.

## 4. Implementation

Add `work/strat26/package_check.py`; export to a short-path folder, include user guide and corpus copies, exclude ignored scratch data and unrelated files, and verify hashes after copying to a clean directory. Record browser/version and test date.

## 5. Experiment and decision

Baseline: exported bundle. Test opening from `file://` with Wi-Fi disabled and all citation links. Proposed gate: 100% cited sources resolve, zero external requests, and clean-copy hashes match; any failure blocks release and triggers a printable PDF fallback.

## 6. Risks

Bundling the full corpus may expose irrelevant content; curate permitted source copies and preserve originals. Hashes guarantee identity, not correctness.

## 7. Combines with

Strategies 1, 7, 10, 21; perform final check on the exact handoff copy.

## 8. Results log

NOT RUN. No bundle, offline test, or hash verification has been created.
