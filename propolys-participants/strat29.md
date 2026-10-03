# Propolys · Strategy 29: BreakGlass Review — bounded emergency access for SaaS admins

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic privilege request and mock approval log |
| Source | NIST CSF 2.0 governance/access outcomes |
| Work folder | `propolys-participants/work/strat29/` |

## 1. Context and local evidence

The [results overview](../RESULTS_OVERVIEW.md) says no Propolys buyer validation has occurred. SnoopWatch detects inappropriate access after the fact, ExitProof handles departure closure, and ProofDesk addresses account recovery. None governs an authorized emergency elevation where an administrator needs temporary privileged access. This idea is not a monitoring product and has not been tested against identity systems or customer change policies. NIST CSF 2.0 is a voluntary risk framework, not an emergency-access rule or market proof.

## 2. Idea and novelty

**BreakGlass Review** is a lightweight approval and evidence workflow for MSPs and internal IT teams granting temporary admin rights during an outage. The requester states purpose, system and duration; policy templates define approvers and scope; AI extracts and summarizes the request, checks it against the approved change record, and flags mismatches. Deterministic enforcement records approvals and expiration evidence; the actual privilege grant remains in the customer's identity system and may be manual in an initial pilot. Revenue assumption: annual fee by managed tenant, with setup services.

Nearest old strategy is SnoopWatch, a post-event access-anomaly investigation system. BreakGlass Review documents a pre-authorized, time-bounded exception, with no patient records or anomaly learning. Novelty is the small-team emergency exception workflow.

## 3. Why it fits the rubric

The story balances incident response speed and least privilege. CSF 2.0 provides broad cybersecurity governance context: [NIST CSF 2.0](https://www.nist.gov/cyberframework). It does not certify this workflow or establish buyer interest.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat29/pitch.md` (three-slide outline and script), `propolys-participants/work/strat29/demo.html` (synthetic click-through), and `propolys-participants/work/strat29/validation.md` (interview guide, baseline and proposed gates).

Slides: urgent fictional outage; request, reviewer, end time and audit trail; MSP buyer and tenant subscription hypothesis. A safe mock demo shows an overbroad request rejected for human review, then a narrower approved scope expiring in the synthetic log. No real privileges change.

## 5. Proposed validation

Interview 8 MSP or internal IT managers. Compare a mock policy flow with their current process on 12 synthetic emergency requests; record completeness, correct approver, scope, expiry and task time. Adopt if 6/8 identify recurring unsystematic exceptions and the mock correctly routes at least 11/12 cases with no auto-approval. Kill if integration cannot guarantee expiration or if workflow adds over 2 minutes to the median simulated approval.

## 6. Risks and limits

The record may say access expired when the identity system did not revoke it. An emergency flow can become a bypass. Enforce independent system confirmation, least privilege, strict scopes, and post-event review. Ensure fail-safe behavior and client-specific governance.

## 7. Combines with

Could coexist with ExitProof, but do not make offboarding a feature of this initial concept.

## 8. Results log

NOT RUN. No customers, identity connectors, security assessment, approval study or real privilege actions. Numeric gates are proposed.
