# Propolys · Strategy 28: CaseSeal — defensible digital evidence handoff

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic evidence files and mock incident case; no real evidence |
| Source | NIST SP 800-86 forensic integration guidance |
| Work folder | `propolys-participants/work/strat28/` |

## 1. Context and local evidence

Local results are explicitly unvalidated in [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). Strategies 7 and 14 organize reports and media provenance; strategy 23 assembles privacy breach facts. This concept addresses a different transfer boundary: a small organization's incident evidence being handed from an internal IT lead to external counsel, an insurer or an investigator, with a record of what was transferred and by whom. The team has not collected, processed or transferred real evidence. NIST forensic guidance is a process reference, not proof of buyer demand.

## 2. Idea and novelty

**CaseSeal** gives an MSP or small security consultancy a case workspace to collect approved files, compute hashes, record source/custodian/time metadata, preserve original files, and generate a manifest for secure handoff. AI suggests duplicate files and extracts candidate timestamps or host identifiers into a reviewable index, always linked to the original; it does not interpret guilt or establish legal admissibility. Buyer: MSP incident-response teams or small firms supporting clients; revenue assumption: per-case fee with an annual team tier.

Nearest old concept is ProvenanceDesk, which helps a newsroom assess public media authenticity. CaseSeal protects controlled evidence custody and handoff during a security incident; it does not fact-check content or decide authenticity.

## 3. Why it fits the rubric

The chain of custody is visual and security-relevant; AI contributes search and indexing, not forensic conclusions. [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final) provides forensic process context. Counsel must determine applicable evidentiary requirements.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat28/pitch.md` (three-slide outline and script), `propolys-participants/work/strat28/demo.html` (synthetic click-through), and `propolys-participants/work/strat28/validation.md` (interview guide, baseline and proposed gates).

Three slides: scattered fictional files; a manifest with hashes and custodian events; MSP buyer, per-case pricing assumption and proposed pilot. Demo three synthetic files with duplicate names and contradictory timestamps; show preserved originals, separate extracted metadata and an explicit discrepancy review. Don't suggest evidence was admissible or chain-of-custody certified.

## 5. Proposed validation

Interview 8 MSP incident responders or digital-forensics consultants. Have each package 10 dummy items using their current process and the mock. Measure time, missing manifest fields and whether they can detect a changed file. Adopt if 6/8 identify repeat manual packaging and every changed test file is detected with all source links preserved. Kill if 3 or more reviewers believe the report overstates admissibility or if customer policy bars the workflow.

## 6. Risks and limits

Hashing detects post-capture changes only; it does not authenticate initial source or collector. Evidence can contain secrets and personal information. Unauthorized access, mistaken custodian metadata, retention rules and legal hold requirements need careful handling.

## 7. Combines with

Can export a controlled packet from BreachBrief but has a separate evidentiary handoff buyer and acceptance test.

## 8. Results log

NOT RUN. No interviews, file tests, forensic validation, legal review or customer trials occurred; metrics are proposed only.
