# Propolys · Strategy 22: ProofDesk — safer employee account recovery

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P1 / 3 h |
| Dependency | Synthetic helpdesk tickets and a sandbox identity workflow |
| Source | CISA phishing guidance; NIST Digital Identity Guidelines (verify final relevant sections before pitch) |
| Work folder | `propolys-participants/work/strat22/` |

## 1. Context and local evidence

The local results overview records no Propolys interviews, pilot or demo; see [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). Old strategies 2 and 6 address impersonation in payment and consumer scam contexts; 9 flags inappropriate record access; 17 scores cyber-insurance risk. None centers on the helpdesk's employee account recovery procedure. This idea concerns a narrow high-consequence workflow: a caller claims a worker lost a device and asks support to reset MFA. No claim is made that the team has tested enterprise identity integrations. CISA guidance recommends phishing-resistant MFA for privileged accounts, but does not itself demonstrate an account-recovery product gap or Québec buyer demand.

## 2. Idea and novelty

**ProofDesk** is a workflow assistant for IT helpdesk managers at mid-sized organizations. On a recovery request, it retrieves the organization's approved proofing policy, checks ticket facts against required steps, flags policy gaps, and presents the support agent with an approved alternative verification path and a time-limited reviewer approval. AI extracts the request facts and maps language to the policy checklist; deterministic rules enforce mandatory proofing steps. It does not decide identity, generate credentials, or approve exceptions autonomously. Buyer pays annual tenant subscription, possibly through an identity integrator; revenue is an assumption.

Nearest concepts are CallBack's payment verification and SnoopWatch's access anomaly review. Novelty lies in front-line recovery policy execution, with a human identity proofing decision, rather than payment authorization or post hoc log anomaly detection.

## 3. Why it fits the rubric

The demo makes the attack path understandable and highlights a security control failure point. The pitch can ground the need for strong authentication in [CISA phishing guidance](https://www.cisa.gov/sites/default/files/2025-03/Phishing%20Guidance%20-%20Stopping%20the%20Attack%20Cycle%20at%20Phase%20One%20508.pdf), while clearly labelling account-recovery workflow demand as unvalidated.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat22/pitch.md` (three-slide outline and script), `propolys-participants/work/strat22/demo.html` (synthetic click-through), and `propolys-participants/work/strat22/validation.md` (interview guide, baseline and proposed gates).

Slide 1: fictional employee locked out and attacker pressure on support. Slide 2: synthetic ticket, policy checklist, flagged missing step, supervisor route. Slide 3: buyer (helpdesk owner), annual subscription assumption, proposed design-partner pilot. A three-minute click-through uses a mock ticket and policy text; no real identity provider or user account is touched.

## 5. Proposed validation

Interview 8 helpdesk/security managers. Ask them to walk through a recent anonymized recovery process; record steps, escalation owner, and policy exceptions. Baseline: manual completion and elapsed time for 10 synthetic ticket-policy pairs reviewed by each participating team. Adopt if 6/8 identify recurring inconsistent policy execution and prototype catches at least 9/10 intentionally seeded missing-step cases with zero auto-approvals. Kill if fewer than 4/8 name an accountable budget owner or teams cannot safely share even synthetic workflow rules.

## 6. Risks and limits

Incorrect guidance can lock out legitimate workers or enable account takeover. Recovery policies differ and can include non-digital checks the AI cannot observe. Strict access controls, audit logs, data minimization, and mandatory human decisions are essential; vendor APIs and jurisdictional requirements need review.

## 7. Combines with

Could connect to AgentShield only as a separate identity workflow; no agent-runtime controls are proposed here.

## 8. Results log

NOT RUN. No interviews, benchmark, product, security test or adoption evidence exists. All counts and thresholds are proposed validation criteria.
