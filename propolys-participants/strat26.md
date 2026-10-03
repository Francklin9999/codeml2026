# Propolys · Strategy 26: VulnRelay — structured intake for vulnerability reports

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic disclosure messages and an isolated intake mailbox |
| Source | CISA coordinated vulnerability disclosure overview |
| Work folder | `propolys-participants/work/strat26/` |

## 1. Context and local evidence

The [results overview](../RESULTS_OVERVIEW.md) records no Propolys market tests. DepGuard (10) screens software packages before installation; RedTeamBox (15) tests chatbots; neither supports an organization receiving good-faith vulnerability reports. This is a product-security operations workflow for a small software vendor that lacks a dedicated PSIRT. It does not discover vulnerabilities, scan third parties or automate exploit reproduction. Local buyer need is unvalidated.

## 2. Idea and novelty

**VulnRelay** gives a software company a secure intake portal and case workflow for external security reports. AI extracts affected product/version, reproduction steps, impact claims and reporter contact preferences into a draft record; deterministic checks detect missing fields, suspected secrets and duplicate case text. A designated human acknowledges, classifies severity, routes to an owner and approves a response. The service records timestamps and safe status updates while avoiding unnecessary personal data retention. Buyer: small SaaS/product vendors; revenue assumption: annual subscription tiered by product count, with policy setup as a service.

Nearest old concept is RedTeamBox's proactive chatbot testing. This begins with an outside reporter and coordinates triage, confidentiality and acknowledgement; it is not an attack-generation tool or runtime security control.

## 3. Why it fits the rubric

AI structures incoming reports while preserving accountable review. CISA describes coordinating vulnerability mitigation and public disclosure with affected vendors; this is process context, not buyer evidence: [CISA CVD overview](https://www.cisa.gov/sites/default/files/2023-02/cisa_2022_year_in_review.pdf).

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat26/pitch.md` (three-slide outline and script), `propolys-participants/work/strat26/demo.html` (synthetic click-through), and `propolys-participants/work/strat26/validation.md` (interview guide, baseline and proposed gates).

Slides: a report lost in a generic inbox; secure case with extracted fields linked to the original; SaaS buyer, annual subscription assumption and 30-day pilot proposal. Demo a fictional email with a missing version and an accidentally included token-shaped string; redact the string, mark it for secret handling, and leave severity unassigned.

## 5. Proposed validation

Interview 8 product-security or engineering leads at small software vendors. Have each classify 10 synthetic reports using their current process and this mock workflow; baseline capture acknowledgement time and required-field completeness. Adopt if 6/8 confirm no owned intake workflow and the prototype achieves 90% field extraction while flagging every seeded secret. Kill if reporters cannot safely communicate through the proposed channel or under 4/8 identify an accountable product owner.

## 6. Risks and limits

Submitted content may be malicious, include exploit details or expose personal data. Acknowledgement is not a fix commitment or legal safe harbor. Reports could be misclassified; keep humans in control, isolate attachments, and publish clear scope and retention terms.

## 7. Combines with

Could generate inputs for DepGuard's package team only for a vendor that owns both processes; avoid implying vulnerability scanning.

## 8. Results log

NOT RUN. No reporter portal, interviews, benchmark, integrations or case handling have been performed. All metrics are proposed.
