# Propolys · Strategy 38: ZoneGuard — explain and review sensitive DNS changes

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic DNS zone snapshots and fictional change tickets |
| Source | CISA DNS infrastructure tampering guidance |
| Work folder | `propolys-participants/work/strat38/` |

## 1. Context and local evidence

The local [results overview](../RESULTS_OVERVIEW.md) contains no validated Propolys results. PatchPilot prioritizes software vulnerabilities, DepGuard checks packages, and AccessDiff compares SaaS entitlements. ZoneGuard concerns a different critical control plane: authorized changes to a small organization's public DNS zone. A hostile or mistaken record can redirect users or interrupt services. No DNS data or provider workflow has been inspected, and the proposal makes no claim about incident frequency or demand.

## 2. Idea and novelty

**ZoneGuard** is a change-review assistant for MSP DNS administrators and small organizations without a dedicated DNS security team. It compares a proposed zone-file/API change with the existing zone and approved ticket, explains material effects such as new nameservers, mail routing or wildcard records, and flags unexplained scope. AI maps ticket prose to change intent and summarizes consequences; deterministic parsing, DNSSEC/signature checks where supported, and human approval govern the actual change. Initial offering is read-only diff plus approval record; later connectors may gate a provider API. Revenue assumption: monthly fee per managed domain.

Nearest old idea is AccessDiff: SaaS identity privilege changes. ZoneGuard examines DNS record and delegation changes, not permissions or user behavior. It is also distinct from SpoofRadar's radio signal interference map.

## 3. Why it fits the rubric

This is a bounded infrastructure integrity workflow. CISA describes DNS record tampering as a way to redirect or intercept traffic and recommends reviewing DNS records; it does not establish demand for this product: [CISA DNS tampering guidance](https://www.cisa.gov/sites/default/files/publications/CISAInsights-Cyber-MitigateDNSInfrastructureTampering_S508C.pdf).

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat38/pitch.md` (three-slide outline and script), `propolys-participants/work/strat38/demo.html` (synthetic click-through), and `propolys-participants/work/strat38/validation.md` (interview guide, baseline and proposed gates).

In `work/strat38/`, make slides for a fictional unauthorized nameserver change, a parsed diff showing the domain impact, and an MSP/domain buyer with per-domain subscription assumption. Demo only a static synthetic zone file and ticket; do not issue DNS updates.

## 5. Proposed validation

Interview 8 MSP DNS operators. Review 20 synthetic changes with seeded unexpected delegation, MX and wildcard edits against a ticket. Adopt if 6/8 report manual review burden and all seeded high-impact changes are surfaced with no more than 2 false escalations in 20 routine cases. Kill if provider APIs cannot preserve approval controls or operators cannot explain the AI-generated change summary.

## 6. Risks and limits

A valid change can be operationally risky; a malicious change can be correctly authorized by a compromised operator. AI could misunderstand DNS semantics. Keep parsing deterministic, updates human-controlled, and rollback/ownership checks explicit.

## 7. Combines with

Could feed an incident response process after a domain event, but no monitoring or automatic domain remediation is in scope.

## 8. Results log

NOT RUN. No DNS operations, interviews, API tests or change benchmark have occurred. Gates are proposed only.
