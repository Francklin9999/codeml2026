# Propolys · Strategy 24: ReleaseCheck — privacy-safe record release review

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic public-record package and human-approved redaction policy |
| Source | NIST Privacy Framework (voluntary guidance; no local demand inferred) |
| Work folder | `propolys-participants/work/strat24/` |

## 1. Context and local evidence

The [local results overview](../RESULTS_OVERVIEW.md) contains no Propolys customer evidence. Earlier DocTrust (8) analyzes submitted documents for authenticity; ProvenanceDesk (14) verifies media origins; BreachBrief (23) assembles incident records. This concept concerns an entirely different point: checking an outgoing record package before an organization releases it externally. The proposed buyer is a municipal access-to-information/privacy office, but no buyer interview or procurement review exists. NIST's Privacy Framework is voluntary risk-management guidance, not a law or proof of product demand.

## 2. Idea and novelty

**ReleaseCheck** checks a draft package of records for accidental disclosure before an authorized employee releases it. It detects likely direct identifiers, credentials, hidden spreadsheet tabs, comments, document metadata and cross-file inconsistent redactions; groups candidate disclosures by file and page; then produces a review queue linking every suggestion to its exact source. A language model can classify ambiguous context such as a name embedded in narrative, while deterministic checks find metadata and hidden structures. A human decides what is withheld and signs off. The product does not decide exemptions or legal entitlement. Revenue assumption: annual organization subscription plus deployment services.

Nearest old idea is DocTrust: input-document fraud screening, whereas ReleaseCheck is outbound disclosure review. The similarity is document parsing only; buyer, risk, decision and workflow differ.

## 3. Why it fits the rubric

Confidentiality protection and AI uncertainty are easy to explain. NIST Privacy Framework can support a general risk-management framing, without asserting a legal mandate or quantified harm: [NIST framework](https://www.nist.gov/privacy-framework).

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat24/pitch.md` (three-slide outline and script), `propolys-participants/work/strat24/demo.html` (synthetic click-through), and `propolys-participants/work/strat24/validation.md` (interview guide, baseline and proposed gates).

Slide 1: fictional spreadsheet with hidden personal data. Slide 2: review pane showing candidate fields and page/metadata provenance, all marked “human review”. Slide 3: privacy-office buyer, annual license assumption, pilot. Use a fabricated dataset and show that the export is blocked pending sign-off; no real records are processed.

## 5. Proposed validation

Interview 8 municipal or institutional privacy-records staff. Compare current checklist review and prototype on 20 synthetic packages containing seeded exposures. Adopt if 6/8 describe repeat work, recall is at least 95% on seeded exposures, and false positive candidates average no more than 3 per package. Kill if any seeded hidden sheet or metadata item escapes, or if reviewers mistake suggestions for legal exemptions.

## 6. Risks and limits

False negatives disclose protected data; false positives delay legitimate release. Language, format and exemption law vary. AI must not make redaction decisions, and processing itself can expose sensitive records. Requires strict retention, access controls, counsel review and accessibility testing.

## 7. Combines with

Could reuse extraction concepts from DocTrust, but maintain distinct release-review purpose and evaluation.

## 8. Results log

NOT RUN. No interviews, package evaluation, legal review, live records, or adoption results exist. Thresholds are proposed.
