# NOVA · Strategy 40: Release freeze and post-event delta acceptance checklist

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (handoff control) |
| **Effort** | 2 h plus event |
| **Depends on** | baseline export, manifest, update workflow |
| **Rubric lines** | update after event; evidence navigation |
| **Work folder** | work/strat40/ |

## 1. Context and evidence

The rubric requires retaining baseline and adding the live event with sourced impacts and actions. Strategies 5 and 23 preserve temporal state; strategy 26 checks the export. This proposal defines a release checkpoint around the actual handoff artifact.

## 2. Idea and novelty

Before the event, freeze and hash baseline deliverables; after integration, generate a delta manifest listing added, changed, and unchanged facts/views, reviewer, and source locator. Unlike the general bitemporal store, this is a practical release checklist that can be completed during a live presentation.

## 3. Rubric

The evaluator can inspect what changed, verify that baseline survives, and see that unrelated conditions were not silently closed.

## 4. Implementation

Create `work/strat40/release_checklist.md`; include baseline hash, event evidence locator, approved status class, affected fact IDs, regenerated files, link checks, and final reviewer. Store separate immutable baseline and updated export directories.

## 5. Experiment and decision

Baseline: final pre-event export. Rehearse with a synthetic event clearly labeled as a fixture, then use actual event only at presentation. Proposed gate: baseline hash unchanged; every changed claim links to event or corroborating source; all unaffected go-live conditions remain visible. Target completion within the allowed event window; if not, publish a manual delta and label automation incomplete.

## 6. Risks

Time pressure encourages unsupported inference; checksum success is not semantic review. Never include rehearsal content in the real project state.

## 7. Combines with

Strategies 5, 6, 23, 25, 26 and 39; final gate for update publication.

## 8. Results log

NOT RUN. No release freeze, rehearsal delta, or live update has been performed.
