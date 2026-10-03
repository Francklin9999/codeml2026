# Propolys · Strategy 25: ExitProof — verified access removal at employee departure

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic identity/app roster and HR departure ticket |
| Source | NIST CSF 2.0 (access-control outcomes; no product mandate) |
| Work folder | `propolys-participants/work/strat25/` |

## 1. Context and local evidence

No Propolys customer research or security pilot is recorded in the [results overview](../RESULTS_OVERVIEW.md). Strategies 9 and 17 consider health-record access anomalies and cyber underwriting; strategy 22 concerns helpdesk account recovery. Employee offboarding is distinct: reconcile an authorized departure event to removal of the departing worker's access across a known app estate. The team has not inspected a real HRIS or identity-provider integration. NIST CSF 2.0 supplies general cybersecurity outcomes, not evidence that a local organization will buy this product.

## 2. Idea and novelty

**ExitProof** is for MSPs managing identity for several mid-sized clients. It ingests a client-approved roster of accounts and app owners plus a departure ticket, proposes a checklist of access to disable, tracks owner acknowledgements, and flags unresolved accounts after the expected cutoff. AI maps inconsistent app labels, usernames and ticket prose to candidate accounts; rules preserve exact identifiers and require a human to approve each action. The first version exports a closure evidence report and does not revoke access automatically. Subscription assumption: fee per managed tenant or departing worker, with integration onboarding.

Nearest old idea is SnoopWatch, which detects suspicious health-record lookups after access; ExitProof checks whether access is removed after a legitimate employment event. PatchPilot ranks vulnerabilities; it does not cover identity lifecycle.

## 3. Why it fits the rubric

Simple “departure ticket to verified closure” demo, identifiable MSP buyer and concrete security objective. [NIST CSF 2.0](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258) offers a framework for access and governance outcomes, but the pitch must present offboarding value as a hypothesis.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat25/pitch.md` (three-slide outline and script), `propolys-participants/work/strat25/demo.html` (synthetic click-through), and `propolys-participants/work/strat25/validation.md` (interview guide, baseline and proposed gates).

Three slides: fictional departure with multiple SaaS accounts; reconciled checklist with one unmatched identity; MSP tenant pricing assumption and design-partner plan. Demo synthetic data only: show an alias match with source records, confidence and human review, then leave one account unresolved. No live deprovisioning.

## 5. Proposed validation

Interview 8 MSP identity administrators. Build a baseline from each team's process on 10 synthetic departure packets with app rosters. Measure missed accounts, duplicate tickets and review minutes. Adopt if 6/8 report manual reconciliation recurring, prototype identifies at least 95% of seeded accounts with zero automatic revocations, and median review time falls 25%. Kill if identity ownership cannot be established from customer-approved sources or under 4/8 identify a buyer budget.

## 6. Risks and limits

Bad identity matching may disable the wrong user; an app missing from inventory remains invisible. Departures can involve legal holds or transitions. Require explicit customer approval, audit trails, least privilege and rollback plan; connectors broaden attack surface.

## 7. Combines with

Could complement ProofDesk for account lifecycle, but recovery and departure are separate workflows and should not be bundled in validation.

## 8. Results log

NOT RUN. No interviews, integration, process comparison or access changes were performed. Numerical thresholds are proposed only.
