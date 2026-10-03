# NOVA · Strategy 23: Live-event change-impact ledger

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (live update control) |
| **Effort** | 4 h |
| **Depends on** | baseline fact IDs and event input |
| **Rubric lines** | update after event; chronology |
| **Work folder** | work/strat23/ |

## 1. Context and evidence

The rubric requires integrating a new event without erasing baseline, distinguishing project status, prior decision, and new proposal. Strategy 5 provides bitemporal storage and strategy 6 drills event handling. This proposal records impact propagation across dependent claims, rather than merely writing a before/after diff.

## 2. Idea and novelty

Represent each event as a typed delta linked to affected and unaffected claims, actions, answers, and brief sections. Show why each dependency changes or stays unchanged. Unlike the general append-only event store, this is a focused impact-review map that catches downstream stale summaries.

## 3. Rubric

Makes the update auditable: the evaluator sees the new evidence, its scope, and why unrelated approvals or conditions remain as they were.

## 4. Implementation

Create `work/strat23/impact_map.yaml` with event ID, source locator, assertion type, valid/record time, linked fact IDs, impact rationale, reviewer, and regenerated views. Build a preflight checklist; never allow an event to overwrite the frozen baseline.

## 5. Experiment and decision

Baseline: strategy 5 state and diff. Drill five hypothetical event types (validation, delay, proposal, rejection, new risk). Adopt if all five preserve the original baseline and identify every affected summary with zero unsupported status changes; target under 5 minutes per drill. Scenarios are practice, not corpus facts.

## 6. Risks

A manually maintained dependency map can become stale. Hypothetical events must be clearly labeled so they are not mistaken for evidence.

## 7. Combines with

Strategies 5, 6, 9, 16–19; integrate only actual live evidence in the final deliverable.

## 8. Results log

NOT RUN. No impact graph, live event, or drill result has been recorded.
