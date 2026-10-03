# Propolys · Strategy 36: AccessDiff — explain meaningful SaaS entitlement changes

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic SaaS group and role snapshots |
| Source | NIST CSF 2.0 governance and access outcomes |
| Work folder | `propolys-participants/work/strat36/` |

## 1. Context and local evidence

No Propolys customer interviews or product tests are recorded in [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). SnoopWatch identifies suspicious patient-record access, ExitProof tracks access removal at departure, and BreakGlass Review (29) records emergency privilege. AccessDiff instead analyzes recurring changes to enterprise SaaS permissions and explains what capability changed, who requested it and which asset is affected. It does not score users for misconduct or automatically revoke permissions. No real identity or SaaS snapshots have been reviewed.

## 2. Idea and novelty

**AccessDiff** serves an IT governance lead or MSP administrator responsible for multiple SaaS applications. It compares approved role/group baselines with current entitlements, translates vendor-specific permission names into plain-language action descriptions using AI, and produces a review queue emphasizing new administrative or export capability. Exact permission values and diffs remain linked to source snapshots; a human owner accepts or corrects mappings. The first product is read-only. Revenue assumption: fee per connected tenant, plus setup for application-role mapping.

Nearest old strategy is SnoopWatch: post hoc analysis of individual EHR record access. AccessDiff is a periodic entitlement-change review, not user-behavior surveillance. ExitProof handles one termination event; AccessDiff considers longitudinal role drift without inferring employment status.

## 3. Why it fits the rubric

The security issue is privilege change visibility; AI makes vendor-specific permission labels reviewable. NIST CSF 2.0 supplies general governance framing only: [NIST CSF 2.0](https://www.nist.gov/cyberframework). It is not a control certification or evidence of buyer demand.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat36/pitch.md` (three-slide outline and script), `propolys-participants/work/strat36/demo.html` (synthetic click-through), and `propolys-participants/work/strat36/validation.md` (interview guide, baseline and proposed gates).

Three slides: a role with hidden export permission; before/after entitlement diff and linked source; MSP governance buyer, per-tenant pricing assumption and pilot. Synthetic demo compares two mock snapshots, explains a changed permission, and requests owner review without changing access.

## 5. Proposed validation

Interview 8 SaaS administrators or MSP leads. Test 20 synthetic before/after role pairs against administrator ground truth. Adopt if 6/8 report recurring manual reviews, 100% of seeded admin/export permission increases are surfaced, and no more than 2 of 20 benign changes are escalated. Kill if administrators cannot validate role semantics from source docs or if permissions are too application-specific for reusable workflow.

## 6. Risks and limits

Role meaning can be contextual and vendor updates change semantics. Mislabeling may overlook privilege or trigger fatigue. Data access itself is sensitive; use read-only least-privilege connectors, approval logs and customer-specific baselines.

## 7. Combines with

Can feed ExitProof for a departure reconciliation, but the standalone periodic change-review use case remains the target.

## 8. Results log

NOT RUN. No interviews, SaaS connectors, role benchmark or live access changes. All gates are proposals.
