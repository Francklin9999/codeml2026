# Propolys · Strategy 27: ClearChain — proof of secure media sanitization

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Mock device inventory, simulated erase logs; no drive erasure |
| Source | NIST SP 800-88 Rev. 2 media sanitization guidance |
| Work folder | `propolys-participants/work/strat27/` |

## 1. Context and local evidence

No Propolys product validation is reported in the [results overview](../RESULTS_OVERVIEW.md). Existing ideas address document fraud, package compromise, logs and recovery; none covers custody and evidence when organizations retire or resell storage devices. The local OptiFrame demo was synthetic geometry, not device handling; no asset destruction or sanitization process was run. NIST SP 800-88 provides media sanitization guidance, but does not validate a buyer or reseller demand.

## 2. Idea and novelty

**ClearChain** is a workflow and evidence service for IT asset disposition firms handling laptops and removable media for schools, clinics and SMEs. It links an authorized asset manifest to chain-of-custody events, approved sanitization method, tool output and independent verification status; exceptions such as failed verification stay quarantined for human resolution. AI reconciles serial-number formats and flags missing evidence or conflicting custody timestamps. Cryptographic hashes protect report integrity; AI never claims that a disk is sanitized. Revenue assumption: per-device processing fee or recurring site license for audit packages.

Nearest old concept is RestoreLedger (21): it verifies service recovery evidence; ClearChain follows physical media through retirement and disposal. It is not a backup monitor, package scanner or document-forgery detector.

## 3. Why it fits the rubric

The security story is confidential data leaving service, with a visible device-to-certificate trail. NIST's [SP 800-88 Rev. 2](https://csrc.nist.gov/pubs/sp/800/88/r2/final) is authoritative sanitization guidance. Product claims must align to approved procedures and customer policy, not infer erasure success from a model.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat27/pitch.md` (three-slide outline and script), `propolys-participants/work/strat27/demo.html` (synthetic click-through), and `propolys-participants/work/strat27/validation.md` (interview guide, baseline and proposed gates).

Slides: device handoff; chain-of-custody ledger with an unresolved serial mismatch; reseller buyer and per-device revenue hypothesis. Show fabricated inventory and simulated logs, one discrepancy, a failed verification state and quarantine. Clearly state no real hardware was erased.

## 5. Proposed validation

Interview 8 ITAD operators or institutional asset managers. Compare their current evidence packet to a mock consolidated record across 20 simulated devices. Adopt if 6/8 report repeated reconciliation work and prototype captures 100% of seeded serial mismatches with zero “sanitized” verdicts absent a valid signed verification event. Kill if operators need hardware certification or chain-of-custody standards the proposed service cannot meet.

## 6. Risks and limits

Log provenance can be falsified; hashes prove unchanged files, not truth. Sanitization depends on media type, tooling and verified procedure. A report may create false assurance or liability. Require secure handling, independent verification, policy mapping and records retention review.

## 7. Combines with

May complement RestoreLedger for end-of-life devices, but product boundary and buyer validation remain distinct.

## 8. Results log

NOT RUN. No interviews, hardware work, sanitization or certification test exists. Proposed test thresholds are not results.
