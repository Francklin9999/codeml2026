# Propolys · Strategy 31: ModelSeal — controlled approval for AI model releases

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic model release manifest and fictional test results |
| Source | NIST AI Risk Management Framework (voluntary guidance) |
| Work folder | `propolys-participants/work/strat31/` |

## 1. Context and local evidence

The [results overview](../RESULTS_OVERVIEW.md) records no Propolys AI-product pilot or buyer interviews. AgentShield (3) protects tool-using agents at runtime; RedTeamBox (15) tests a chatbot before deployment. ModelSeal addresses the distinct software-release workflow for teams that update an AI model or retrieval corpus: maintain approved artifact identity and evidence before rollout. It does not stop prompt injection, guarantee model behavior or certify safety. NIST AI RMF is voluntary trustworthiness guidance, not a compliance certification or evidence of customer demand.

## 2. Idea and novelty

**ModelSeal** is a release-evidence workspace for a small enterprise AI platform team. It ties a model/configuration/data snapshot hash to owner, intended use, evaluation report version, approval and rollout environment. AI summarizes differences between release notes and test evidence, flags missing evidence categories and links claims to source files; deterministic signature and hash checks detect artifact substitutions. A human release owner approves or blocks the change. Buyer: organizations with internal AI deployments; revenue assumption: annual team subscription, with private deployment option.

Nearest old strategy is RedTeamBox, which probes chatbot responses for vulnerabilities. ModelSeal tracks whether the exact artifact reviewed is the one promoted and whether the release packet is complete; it does not generate attacks or evaluate output quality itself.

## 3. Why it fits the rubric

This connects security to the integrity and governance of AI changes. Use [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) only to frame risk-management vocabulary. It is voluntary guidance and cannot be described as a customer mandate or certification.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat31/pitch.md` (three-slide outline and script), `propolys-participants/work/strat31/demo.html` (synthetic click-through), and `propolys-participants/work/strat31/validation.md` (interview guide, baseline and proposed gates).

Slides: two similarly named model files; release evidence with a hash mismatch; platform-team buyer, subscription assumption and proposed pilot. Synthetic demo modifies one byte in a fake artifact manifest and shows verification failure while leaving behavior approval to a human.

## 5. Proposed validation

Interview 8 AI platform/security leads. Compare current release packets with a mock checklist over 12 synthetic releases. Adopt if 6/8 report manual artifact/evidence reconciliation and prototype detects all seeded hash substitutions and flags at least 90% of seeded missing approval/evaluation records, with zero “safe” verdicts. Kill if teams already have an integrated artifact control that resolves this need or the proposed hashes cannot map to real deployments.

## 6. Risks and limits

Hashes prove byte identity only, not source trust, evaluation validity or safe model behavior. Evaluation evidence can be cherry-picked. Model/data confidentiality, reproducibility and evolving standards need technical review. Require signed sources and independent release approval.

## 7. Combines with

Could link to RedTeamBox's report as one release artifact, not a replacement or bundled promise.

## 8. Results log

NOT RUN. No model releases, test corpus, interviews, security assessment or customer adoption. All thresholds are proposed.
