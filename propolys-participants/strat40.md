# Propolys · Strategy 40: ConsentMap — constrain approved data use in AI workflows

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic dataset labels and mock AI pipeline manifest |
| Source | NIST AI RMF; voluntary risk-management resource |
| Work folder | `propolys-participants/work/strat40/` |

## 1. Context and local evidence

No Propolys product or buyer findings are recorded in [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). AgentShield protects agent tool use, RedTeamBox probes chatbot behavior, and ModelSeal tracks release artifact identity. ConsentMap covers a different AI security boundary: whether a dataset approved for one purpose is being reused in another pipeline or external model service. No real data governance system has been inspected, and legal authority/consent is a human-owned question rather than an AI decision.

## 2. Idea and novelty

**ConsentMap** serves a data governance lead at a health, education or financial organization. It links datasets to documented purpose, sensitivity, permitted environment, owner and expiry; compares a proposed AI pipeline manifest and data lineage to those attributes; and flags missing approval or incompatible use for review. AI extracts candidate labels from data dictionaries and policy text with direct citations; deterministic rules implement the approved organization's own policy. It does not infer legal consent or authorize processing. Revenue assumption: annual enterprise subscription with private deployment and integration services.

Nearest existing concept is ModelSeal, which proves which model artifact passed a release workflow. ConsentMap governs permitted dataset/purpose routing before development and model execution; it does not evaluate model risk or artifact integrity.

## 3. Why it fits the rubric

An understandable “this dataset is approved here, not there” demo ties AI utility directly to data security and governance. NIST AI RMF offers voluntary AI risk-management context: [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework). It is not certification and does not establish local law or buyer demand.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat40/pitch.md` (three-slide outline and script), `propolys-participants/work/strat40/demo.html` (synthetic click-through), and `propolys-participants/work/strat40/validation.md` (interview guide, baseline and proposed gates).

In `work/strat40/`, prepare three slides: dataset label and requested pipeline; source-linked policy mismatch; governance buyer, annual subscription assumption and pilot. Demo synthetic metadata only, with a human reviewer resolving ambiguous purpose; no live data is sent to an AI service.

## 5. Proposed validation

Interview 8 data governance or AI platform leads. Assess 20 synthetic dataset-pipeline pairings against an organization-authored ruleset. Adopt if 6/8 report repeated manual mapping and the mock catches all seeded prohibited-purpose/environment conflicts while allowing at least 16/20 valid pairs. Kill if source policies cannot be expressed as auditable rules or reviewers interpret flags as legal approval.

## 6. Risks and limits

Labels may be stale or incomplete, lineage can be missing, and policies differ by context. A false approval could expose sensitive data; a false block could delay work. Require data-owner sign-off, versioned policy and access-controlled metadata.

## 7. Combines with

Could contribute an approved dataset manifest to ModelSeal's release packet, while retaining separate data-use and artifact-integrity decisions.

## 8. Results log

NOT RUN. No policy interviews, dataset integrations, legal review or model pipeline test completed. Proposed thresholds only.
