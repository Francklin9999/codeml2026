# Propolys · Strategy 33: DataExpiry — verified deletion of sensitive working copies

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic retention schedule and test files |
| Source | OPC PIPEDA breach guidance; scope limited to covered organizations |
| Work folder | `propolys-participants/work/strat33/` |

## 1. Context and local evidence

The local [results overview](../RESULTS_OVERVIEW.md) contains no Propolys customer results. ReleaseCheck (24) checks an outgoing disclosure package; ExitProof (25) reconciles worker identity access; BreachBrief (23) assembles a breach record. DataExpiry addresses the separate security control of finding and removing sensitive temporary working copies when an organization-approved retention period ends. It does not state what a lawful retention schedule is. OPC guidance for organizations subject to PIPEDA requires breach records to be retained for the prescribed period, illustrating why deletion must respect policy exceptions rather than indiscriminately erase data; this does not create a general product mandate.

## 2. Idea and novelty

**DataExpiry** is for privacy operations and IT owners at a small financial or professional-services firm. It maps an approved retention schedule to copies in designated storage locations, discovers candidate files by metadata and content class, and presents a deletion queue with legal hold and business-owner exceptions. AI classifies likely document categories and explains matches; fixed rules enforce dates and require a named approver. Connectors report completion evidence where available; they do not pretend to prove unrecoverable deletion from backups. Revenue assumption: annual fee by connected repository.

Nearest old idea is DocTrust, which screens documents at intake. DataExpiry is lifecycle closure for retained copies, not document authenticity screening or outbound redaction.

## 3. Why it fits the rubric

The idea links AI-assisted discovery to reducing retained exposure while keeping retention judgment with the organization's policy owner. OPC's [PIPEDA breach guidance](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/privacy-breaches-at-your-business/gd_pb_201810/?seq_no=2) is used narrowly: it describes obligations for PIPEDA-covered organizations; it is not proof of demand.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat33/pitch.md` (three-slide outline and script), `propolys-participants/work/strat33/demo.html` (synthetic click-through), and `propolys-participants/work/strat33/validation.md` (interview guide, baseline and proposed gates).

Three slides: duplicate fictional sensitive files in two repositories; candidate deletion queue with a legal-hold exception and owner approval; privacy/IT buyer and repository subscription assumption. Demo a fake dataset showing policy date, matched copies, and deletion status separately from unverified backup copies.

## 5. Proposed validation

Interview 8 privacy or records managers. On synthetic data with 50 files and seeded holds/duplicates, compare the mock to a manual inventory. Adopt if 6/8 identify recurring repository reconciliation and the queue finds at least 95% of seeded in-scope files while excluding every seeded legal hold. Kill if a connector cannot reliably identify versions or a reviewer assumes deletion from a backup is proven.

## 6. Risks and limits

Deleting records improperly can harm operations or violate retention duties. Content classifiers can miss, overclassify or expose data. Backups, caches and third parties complicate deletion verification; scope and jurisdiction-specific advice are essential.

## 7. Combines with

ReleaseCheck may flag copies to retain during a release project, but separate buyer workflows should be validated independently.

## 8. Results log

NOT RUN. No repository scan, customer interview, deletion or legal review has occurred. Proposed metrics are not results.
