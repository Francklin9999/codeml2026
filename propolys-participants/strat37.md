# Propolys · Strategy 37: PublicSession — safer shared-computer session cleanup

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Synthetic kiosk browser and reset-event logs |
| Source | NIST SP 800-53 session-termination controls |
| Work folder | `propolys-participants/work/strat37/` |

## 1. Context and local evidence

The local [results overview](../RESULTS_OVERVIEW.md) reports no Propolys customer trials. Prior concepts focus on enterprise access governance, source authenticity, identity recovery, incidents and infrastructure. PublicSession targets shared public-access computers in libraries or community centers where one patron's session can leave residual state for the next user. No local observation of residual exposure is claimed. This is a proposed endpoint assurance workflow, not a surveillance system or a general endpoint security suite.

## 2. Idea and novelty

**PublicSession** helps a public library IT lead verify that shared browsers return to a known state between patrons. It combines a signed reset policy, browser/OS event summaries, synthetic test sessions and a staff exception queue. AI clusters unfamiliar residual artifacts into “likely cached identity/session” versus benign kiosk residue, but exact indicators and a human review determine action. It does not inspect patron browsing content. Buyer: municipal or library IT department; revenue assumption: per-terminal annual license with deployment services.

Nearest old concept is SnoopWatch, which finds inappropriate staff access to health records. PublicSession is device-state verification between anonymous public sessions, not monitoring who accessed which record. Nearest technical adjacent concept is RestoreLedger, but this focuses on workstation session boundaries rather than backups or service restoration.

## 3. Why it fits the rubric

Protects privacy and account security in an intuitive setting. NIST SP 800-53 includes session-termination controls; this does not establish public-kiosk demand: [NIST SP 800-53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final).

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat37/pitch.md` (three-slide outline and script), `propolys-participants/work/strat37/demo.html` (synthetic click-through), and `propolys-participants/work/strat37/validation.md` (interview guide, baseline and proposed gates).

In `work/strat37/`, prepare three slides: patron sign-out; synthetic reset check with one residual session marker; library IT buyer, per-terminal subscription hypothesis and pilot. Demo a mock log only, with no real patron history or actual kiosk control.

## 5. Proposed validation

Interview 8 library/community-center IT administrators. Compare existing sign-out/reset practice with a mock workflow using 20 seeded test sessions. Baseline current manual verification steps. Adopt if 6/8 report a recurring assurance gap and prototype detects all seeded residual authentication artifacts while generating no more than 2 benign alerts per 20 clean sessions. Kill if institutions cannot run test sessions safely or if existing kiosk software already verifies cleanup.

## 6. Risks and limits

Event logs may not reveal browser state; the tool may create false confidence. Avoid collecting patron identity or browsing history. Require controlled tests, privacy review, least-privilege access and a human release decision.

## 7. Combines with

Could integrate with existing kiosk management, but it is not an identity directory or SaaS entitlement review.

## 8. Results log

NOT RUN. No interviews, kiosk tests, log access or deployments exist. The proposed sample sizes and thresholds are future gates.
