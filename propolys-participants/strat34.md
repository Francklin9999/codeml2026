# Propolys · Strategy 34: LogSieve — safe diagnostic bundles for software support

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic logs with seeded tokens and personal identifiers |
| Source | NIST SSDF secure development guidance |
| Work folder | `propolys-participants/work/strat34/` |

## 1. Context and local evidence

No customer, product or test evidence exists for Propolys per [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). ReleaseCheck (24) reviews record packages for public disclosure, ShareSafe (30) controls incident artifact exchange, and RedTeamBox (15) tests chatbot behavior. LogSieve concerns a narrower routine workflow: an IT team attaching diagnostic logs to a vendor support ticket, where secrets and personal data may be inadvertently included. The idea does not scan production systems or certify privacy compliance. Local teams have not been interviewed.

## 2. Idea and novelty

**LogSieve** is a pre-upload review tool for SaaS operations teams and MSP helpdesks. A user selects a support bundle; the tool detects likely API keys, tokens, email addresses and internal hostnames, then proposes a redacted copy while preserving log structure needed for troubleshooting. AI handles ambiguous context and explains suggested masks; deterministic secret-pattern rules and checksums preserve original/derived file distinction. A human approves every redaction and destination. Buyer: MSP or software operations team; revenue assumption: per-seat or per-tenant subscription.

Nearest old concept is ReleaseCheck, which audits record disclosure packages under privacy review. LogSieve specifically enables operational troubleshooting while preventing credentials from being sent to a vendor; its usability target is diagnostic fidelity after masking, not identifying protected records for release.

## 3. Why it fits the rubric

The security value is tangible—avoid leaking credentials through an ordinary support process. NIST SSDF is a process reference for secure software development, not evidence of market demand: [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final).

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat34/pitch.md` (three-slide outline and script), `propolys-participants/work/strat34/demo.html` (synthetic click-through), and `propolys-participants/work/strat34/validation.md` (interview guide, baseline and proposed gates).

Slide 1: fictional trace containing a token; slide 2: redacted preview with preserved error context and exact source pointer; slide 3: MSP/operations buyer and subscription assumption. Demo synthetic log only; show a deliberate false positive that a human can restore, documenting the trade-off.

## 5. Proposed validation

Interview 8 MSP support leads or SaaS operators. Compare current manual review to the mock on 30 synthetic log bundles with seeded secrets and diagnostic fields. Adopt if 6/8 report recurring manual review and all seeded secrets are flagged while at least 95% of required diagnostic fields remain usable in a blinded support task. Kill if reviewers find any secret missed or cannot troubleshoot with the redacted output.

## 6. Risks and limits

Unknown secret formats and encoded values evade detectors. Redacted logs may become useless or retain sensitive context. Originals must not be uploaded until policy allows it; retention, access controls and vendor terms need review.

## 7. Combines with

ShareSafe may transfer the approved derived bundle, but redaction is evaluated separately from transfer controls.

## 8. Results log

NOT RUN. No logs, customers, uploads, connectors or redaction benchmark have been tested. Thresholds are prospective only.
