# Propolys · Strategy 21: RestoreLedger — evidence-led recovery drills for MSPs

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P1 / 3 h pitch preparation |
| Dependency | Sanitized backup-job exports and a sandbox restore target; no production restore |
| Source | NIST SP 800-184; NIST CSF 2.0 recovery outcomes |
| Work folder | `propolys-participants/work/strat21/` |

## 1. Context and local evidence

The local Propolys materials show no completed customer work or validated results; see [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). Existing strategies cover OT anomaly detection (4), SOC alert triage (5), crisis coordination (7), and vulnerability prioritization (18), but not proving whether a backup can actually restore an agreed business service. The team has demonstrated synthetic-only data and schema/evaluator work elsewhere, not real OCR or customer operations. The pitch should describe only a proposed drill workflow. NIST's recovery guidance addresses planning, testing and improvement; CSF 2.0 includes verifying restoration assets before use. Neither source establishes local demand.

## 2. Idea and novelty

**RestoreLedger** serves MSP service-delivery leads responsible for several small-business tenants. It turns backup logs, asset inventories and scheduled sandbox restore results into a customer-readable recovery evidence packet: what was selected, what restored, integrity/checksum status, elapsed time, unresolved dependencies, and owner sign-off. AI maps inconsistent vendor job names to a reviewed asset/service catalog, detects missing evidence, and drafts a cited exception summary; deterministic checks validate timestamps and file hashes. It never declares a system “clean” or initiates a production restore. Revenue assumption: monthly fee per tenant plus onboarding to map backup products and recovery objectives.

Nearest old ideas are TriageCopilot's alert explanation and WaterSentinel's operational monitoring. The distinct mechanism is recurring, controlled recovery evidence for backup service assurance—not incident alert prioritization, live plant monitoring, or patch ranking.

## 3. Why it fits the rubric

Buyer and recurring service are identifiable; the security value is tested recoverability. A before/after restore manifest is a concrete, legible demo. Cite [NIST SP 800-184](https://csrc.nist.gov/pubs/sp/800/184/final) for recovery planning/testing and [NIST CSF 2.0](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258) for backup integrity verification; these are guidance, not proof of market demand.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat21/pitch.md` (three-slide outline and script), `propolys-participants/work/strat21/demo.html` (synthetic click-through), and `propolys-participants/work/strat21/validation.md` (interview guide, baseline and proposed gates).

Create three slides: backup green check versus service evidence gap; sample restore ledger with one unresolved dependency; MSP buyer, per-tenant subscription assumption, and proposed pilot. Demo with fabricated, clearly labelled logs: normalize job labels, map to a synthetic service catalog, show one stale restore and source rows. Do not claim a real integration or recovery test.

## 5. Proposed validation

Interview 8 MSP operations leads. Compare their current monthly backup report with the proposed evidence packet; measure time to answer “can this named service be restored?” Baseline: each participant performs the answer task from their own sanitized report. Adopt only if at least 6/8 report recurring manual work and at least 5/8 complete the packet task in under 5 minutes with zero unsupported fields. Kill if fewer than 4/8 identify a buyer-owned budget or if restore evidence requires production access.

## 6. Risks and limits

Logs can be incomplete, vendor-specific or misleading; hashes do not establish malware-free content. AI mappings need human approval. Snapshot/restore handling carries confidentiality and availability risk. A sandbox can differ from production; legal, privacy and retention requirements vary by customer.

## 7. Combines with

Could complement PatchPilot only as a separate recovery workflow; do not fold remediation ranking into the initial product.

## 8. Results log

NOT RUN. No interviews, benchmark, integration, drill, or adoption evidence exists. Proposed numerical thresholds above are future decision rules, not results.
