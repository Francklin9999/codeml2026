# Propolys · Strategy 30: ShareSafe — controlled transfer of incident artifacts

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Mock recipient list, synthetic incident artifacts |
| Source | NIST CSF 2.0 recovery communications outcomes |
| Work folder | `propolys-participants/work/strat30/` |

## 1. Context and local evidence

There is no Propolys product or customer evidence to cite locally; [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md) records that gap. CaseSeal (28) packages evidence with custody metadata; BreachBrief (23) assembles a privacy incident file. ShareSafe focuses on the operational action of sending selected artifacts to a particular outside recipient under a time-limited, approved transfer policy. No real recipient workflows have been observed.

## 2. Idea and novelty

**ShareSafe** helps a small incident-response team exchange files with a named external responder, counsel or insurer. The sender selects an approved case bundle and recipient; the system checks classification labels, recipient-domain allowlist, expiry and required reviewer. AI suggests likely sensitive items based on content and prior labels, then shows exact source snippets; deterministic rules block unapproved domains and expired links. Human reviewers control release. Revenue assumption: per-case fee or subscription for MSP response teams.

Nearest concepts are CaseSeal and ReleaseCheck. CaseSeal preserves evidence custody; ReleaseCheck reviews packages leaving an organization under records rules. ShareSafe is recipient- and time-bound exchange, with revocation and access receipt as its core mechanism. It does not perform forensic authenticity checks or determine legal disclosure rights.

## 3. Why it fits the rubric

Concrete breach-response security workflow and a visual demo of wrong recipient, restricted item and expiration. NIST CSF 2.0 includes recovery communication outcomes, which can frame coordination generally: [NIST CSF 2.0](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258). It is not evidence of product demand.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat30/pitch.md` (three-slide outline and script), `propolys-participants/work/strat30/demo.html` (synthetic click-through), and `propolys-participants/work/strat30/validation.md` (interview guide, baseline and proposed gates).

Show a fictional response team preparing a packet, AI suggesting a sensitive credential file, policy blocking an unapproved recipient, then an approved expiring transfer with access receipt. Three slides: risk moment, control flow, MSP buyer/pricing hypothesis and proposed pilot. Data and transfer are simulated.

## 5. Proposed validation

Interview 8 MSP incident leads. Use 15 synthetic transfer scenarios; compare their current tool flow with mock workflow. Adopt if 6/8 report recurring cross-org file exchange and the mock blocks all seeded wrong-recipient and expired-link cases with median added task time below 90 seconds. Kill if reviewers cannot see an auditable revocation state or if their existing secure portals already solve this with less friction.

## 6. Risks and limits

Content labeling misses secrets; recipient identity can be spoofed; revocation cannot recall downloaded copies. Legal holds, evidence integrity, encryption, retention and customer security review require expert validation. Do not claim end-to-end assurance from AI classification.

## 7. Combines with

Could export CaseSeal manifests, while keeping controlled transfer as separate functionality and buyer test.

## 8. Results log

NOT RUN. No interviews, integration, transfer benchmark or customer test. Proposed thresholds are not evidence.
