# Propolys · Strategy 23: BreachBrief — evidence assembly for privacy incident leads

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P1 / 3 h |
| Dependency | Fictional incident packet; counsel-approved templates needed before real use |
| Source | Office of the Privacy Commissioner of Canada breach guidance |
| Work folder | `propolys-participants/work/strat23/` |

## 1. Context and local evidence

The local [results overview](../RESULTS_OVERVIEW.md) reports no Propolys customer validation. Strategies 5 and 7 summarize security alerts and crisis reports; strategy 9 audits access logs; strategy 14 tracks media authenticity. None is specifically a controlled privacy-breach record and evidence packet for a privacy officer. The Office of the Privacy Commissioner of Canada says PIPEDA-subject organizations must keep records of all breaches, and report breaches that create a real risk of significant harm; requirements depend on jurisdiction and facts. This is a source-grounded workflow premise, not a claim that any named prospective buyer has a problem or that the tool can make legal determinations.

## 2. Idea and novelty

**BreachBrief** helps a privacy officer at a Canadian mid-market organization assemble a reviewable incident file from internal tickets, affected-system notes, timestamps, data-category inventories and mitigation updates. It builds a source-linked chronology, marks unknowns and conflicting statements, and drafts a checklist of fields for a human to complete. AI extracts candidate facts and links each one back to source text; fixed validation rules flag missing dates or required fields. It does not decide whether a report is legally required, estimate harm, contact regulators or notify individuals. Revenue assumption: annual subscription for privacy teams, with a fixed setup fee for templates and access controls.

Nearest old idea is CrisisLens, which consolidates public-safety reports for municipal command. The distinct workflow is private incident evidence management for a privacy officer and legal reviewer, not live emergency situational awareness or alert triage.

## 3. Why it fits the rubric

There is a crisp, source-backed workflow and a trustworthy AI role: organize evidence, leave judgment to accountable staff. OPC guidance gives concrete reporting and record contents: [breach reporting obligations](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/privacy-breaches-at-your-business/gd_pb_201810/?seq_no=2). Scope is explicitly limited to organizations covered by PIPEDA; no general Canadian-law claim.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat23/pitch.md` (three-slide outline and script), `propolys-participants/work/strat23/demo.html` (synthetic click-through), and `propolys-participants/work/strat23/validation.md` (interview guide, baseline and proposed gates).

Three slides: scattered fictional incident notes; source-linked chronology plus “unknown” fields; proposed privacy-officer subscription and pilot. In a 60-second demo, add three fabricated notes with conflicting discovery times and show provenance, conflict flags, and an unfilled legal assessment field. Show no real personal data or regulator submission.

## 5. Proposed validation

Interview 8 privacy officers or breach-response counsel. Use 10 fictional packet scenarios and record manual time to build chronology and completeness. Adopt if 6/8 confirm this assembly is a recurring task and the prototype reduces median completion time by 30% while preserving 100% source links and flagging all seeded conflicts. Kill if counsel sees the output as likely to be mistaken for legal advice or fewer than 4/8 can identify a purchasing route.

## 6. Risks and limits

False completeness may be dangerous; source omission, changed facts and cross-border rules need human handling. Sensitive incident data creates high confidentiality risk. PIPEDA scope is not universal; provincial laws and sector rules require counsel review.

## 7. Combines with

Potentially complements SnoopWatch only at incident documentation stage; no access monitoring is included.

## 8. Results log

NOT RUN. No interviews, timing study, workflow test, legal review or customer demand is evidenced. The validation values are proposed thresholds only.
