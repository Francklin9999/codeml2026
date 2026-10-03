# NOVA · Strategy 22: Evidence lifecycle coverage matrix

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (claim completeness) |
| **Effort** | 3–4 h |
| **Depends on** | curated facts and source inventory |
| **Rubric lines** | chronology; contradictions; evidence |
| **Work folder** | work/strat22/ |

## 1. Context and evidence

The corpus includes emails, meetings, tickets, plans, contracts, invoices, architecture records, chats, and distractors. Strategies 3–4 focus on authority and claim lifecycle; the proposed matrix makes source coverage explicit across important subjects and lifecycle states. There is currently no completed ledger to count.

## 2. Idea and novelty

Build a subject × lifecycle matrix showing which claims have evidence for proposal, decision, delivery, validation, and current status, and which primary/derived source supports each. Mark “not evidenced” rather than infer a missing transition. This differs from strategy 10's file-by-file source triage and strategy 4's per-item state machine: it exposes cross-subject evidence gaps in one review view.

## 3. Rubric

The matrix helps reviewers see unresolved evidence gaps and prevents a delivered ticket from being described as accepted project-wide.

## 4. Implementation

Create `work/strat22/coverage.csv` and a render view over fact IDs. Scope subjects to Q01–Q10 plus go-live conditions; cite fact IDs and source locators in every populated cell.

## 5. Experiment and decision

Baseline: facts used by the answer set. Require 100% of answer claims to trace to a locator and explicitly label unsupported lifecycle cells; zero blank cells may be silently rendered as “complete.” Adopt only if a second reviewer finds no claim whose state exceeds its evidence.

## 6. Risks

Completeness is limited to the corpus and cutoff time. A dense matrix can imply that every subject needs every lifecycle stage.

## 7. Combines with

Strategies 1, 3, 4, 10, 16; feed uncovered cells into strategy 19's unknowns list.

## 8. Results log

NOT RUN. No coverage matrix or claim completeness result exists.
