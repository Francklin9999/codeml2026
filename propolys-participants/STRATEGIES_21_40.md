# Propolys strategies 21–40

All items are proposals, not validated startups. [Local results overview](../RESULTS_OVERVIEW.md) records no completed Propolys research, interviews, product demos or pilots. Challenge deliverable remains a three-minute pitch with up to three slides. Every concept specifies a proposed buyer, AI role, revenue assumption, demo and adopt/kill thresholds. Numeric gates are future validation criteria, not observed results.

| # | Concept | Buyer | AI role | Nearest old concept | Proposed validation gate |
|---:|---|---|---|---|---|
| 21 | RestoreLedger — backup recovery drill evidence | MSP service-delivery lead | Map backup job labels; flag missing evidence | 5 TriageCopilot / 4 WaterSentinel | 8 MSP leads; adopt if 6 report recurring work, 5 finish evidence task under 5 min |
| 22 | ProofDesk — employee account recovery workflow | IT helpdesk manager | Extract ticket facts and map to recovery policy | 2 CallBack | 8 managers; catch ≥9/10 seeded missing steps; zero auto-approvals |
| 23 | BreachBrief — privacy-incident record assembly | Privacy officer | Source-linked fact extraction and chronology | 7 CrisisLens | 8 officers/counsel; ≥30% median assembly-time reduction, complete source links |
| 24 | ReleaseCheck — pre-release records disclosure review | Municipal privacy/records office | Contextual PII suggestions with provenance | 8 DocTrust | 8 staff; ≥95% seeded exposure recall; ≤3 false candidates/package |
| 25 | ExitProof — access removal at departure | MSP identity administrator | Reconcile aliases and app labels to ticket | 9 SnoopWatch | 8 administrators; ≥95% match recall; zero automatic revocations |
| 26 | VulnRelay — external vulnerability-report intake | Small software vendor product-security lead | Extract report fields and identify secrets/duplicates | 15 RedTeamBox | 8 leads; 90% field extraction; flag every seeded secret |
| 27 | ClearChain — media sanitization custody records | IT asset disposition operator | Reconcile serials and flag custody gaps | 10 DepGuard (software supply-chain is a distant adjacent) | 8 operators; catch all seeded serial mismatches; no unsupported sanitize verdict |
| 28 | CaseSeal — incident-evidence custody manifest | MSP incident responder | Index files and suggest duplicates/metadata | 14 ProvenanceDesk | 8 responders; detect every changed test file and preserve source links |
| 29 | BreakGlass Review — temporary SaaS admin exception | MSP / internal IT manager | Summarize request and flag scope mismatch | 9 SnoopWatch | 8 managers; ≥11/12 correct routing; no auto-approval |
| 30 | ShareSafe — recipient- and time-bounded artifact transfer | MSP incident lead | Suggest sensitive items before human release | 5 TriageCopilot (security incident workflow) | 8 leads; block all seeded wrong-recipient/expired-link cases; <90 sec added time |
| 31 | ModelSeal — AI model release artifact integrity | AI platform security lead | Compare release notes and evidence claims | 15 RedTeamBox | 8 leads; catch all seeded hash mismatches, zero “safe” verdicts |
| 32 | SignScan — fixed QR sign inventory/tamper check | Campus facilities/security | Prioritize image/placement mismatches | 11 SkyWatch | 8 staff; detect all seeded destination swaps; accept ≥27/30 valid codes |
| 33 | DataExpiry — approved deletion queue for working copies | Privacy/records manager | Classify files against owner-approved schedule | 8 DocTrust | 8 managers; find ≥95% in-scope files; exclude every seeded legal hold |
| 34 | LogSieve — scrub diagnostic bundles before vendor support | MSP support lead | Contextual secret suggestions with source link | 3 AgentShield (data-exfiltration protection) | 8 leads; flag all seeded secrets; preserve ≥95% diagnostic fields |
| 35 | FirmwareWitness — firmware update provenance intake | Industrial maintenance manager | Summarize release note and flag model mismatch | 10 DepGuard | 8 managers; flag all seeded mismatches and verify valid test signatures |
| 36 | AccessDiff — explain SaaS entitlement changes | SaaS administrator / MSP | Translate vendor permission changes | 9 SnoopWatch / 25 ExitProof | 8 admins; surface all seeded admin/export increases; ≤2/20 benign escalations |
| 37 | PublicSession — shared-computer session cleanup assurance | Library IT administrator | Cluster unfamiliar residual-state indicators | 9 SnoopWatch | 8 admins; detect all seeded auth residue; ≤2 benign alerts/20 sessions |
| 38 | ZoneGuard — DNS change review | MSP DNS administrator | Map ticket intent to parsed zone diff | 4 WaterSentinel (critical-infrastructure security) | 8 operators; surface all seeded high-impact changes; ≤2/20 false escalations |
| 39 | PartTrace — physical replacement part reconciliation | Maintenance/receiving lead | Extract part, serial and lot from varied documents | 1 ProcureGuard / 8 DocTrust | 8 leads; flag all seeded identifier mismatch; ≤3/30 false holds |
| 40 | ConsentMap — dataset purpose/environment policy check | Data governance lead | Extract cited labels from policies/data dictionaries | 3 AgentShield (AI data-leak controls) | 8 leads; catch all seeded use conflicts; allow ≥16/20 valid pairs |

## Priority three: source-grounded rationale

1. **RestoreLedger (21):** NIST recovery guidance explicitly covers planning, testing and improving recovery, while CSF 2.0 includes verifying backup/restoration asset integrity. That supports the proposed recovery-evidence workflow's relevance; neither source shows MSP demand or validates the product. [NIST SP 800-184](https://csrc.nist.gov/pubs/sp/800/184/final) · [NIST CSF 2.0](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957258)
2. **ProofDesk (22):** CISA phishing guidance discusses prioritizing phishing-resistant MFA, including for privileged accounts. That grounds the strong-authentication context, but does not specify account recovery or prove the suggested helpdesk workflow is needed. [CISA phishing guidance](https://www.cisa.gov/sites/default/files/2025-03/Phishing%20Guidance%20-%20Stopping%20the%20Attack%20Cycle%20at%20Phase%20One%20508.pdf)
3. **BreachBrief (23):** OPC guidance states that PIPEDA-subject organizations keep records of all breaches and report those meeting the real-risk-of-significant-harm threshold. That directly supports a record-assembly workflow for this bounded scope; it does not justify automated legal decisions or imply all Canadian organizations are subject to PIPEDA. [OPC breach guidance](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/privacy-breaches-at-your-business/gd_pb_201810/?seq_no=2)

## Evidence and novelty boundary

The official material above is primary-source context only. No market-size, demand, ROI, interview, test or execution result is claimed. Distinction checks: 21 tests service restore ability; 23 assembles incident facts for a privacy officer; 28 records evidence custody; 30 governs the recipient and expiry of a file transfer; 33 finds copies subject to deletion policy. They concern separate data, decisions and evaluation tasks. AI functions are proposals; rules, source links and human approvals constrain consequential actions.
