# NOVA · Strategy 31: High-risk fact verification queue

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (review time allocation) |
| **Effort** | 2–3 h |
| **Depends on** | preliminary fact ledger |
| **Rubric lines** | answer accuracy; budget and approval claims |
| **Work folder** | work/strat31/ |

## 1. Context and evidence

The corpus has duplicated attachments, derived documents, stale records, and distractors. A second reviewer may have limited time. Existing strategies classify all sources and review answer nuance; this proposal prioritizes verification effort by consequence and ambiguity rather than by document order.

## 2. Idea and novelty

Rank facts by impact if wrong, source ambiguity, contradiction count, and numeric/date sensitivity; require primary-source recheck for high-risk claims first. Unlike strategy 10's full source triage, it allocates review capacity at the claim level; unlike strategy 24's source-quality scores, it determines review order rather than citation acceptability.

## 3. Rubric

Focuses scarce verification time on consequential statements such as approval, financial totals, and conditions.

## 4. Implementation

Create `work/strat31/review_queue.csv` with rationale, reviewer, source locator, and disposition. Do not hide lower-ranked facts; all answer citations still receive a final check. Threshold categories are qualitative and fixed before review.

## 5. Experiment and decision

Baseline: all facts used by Q01–Q10. Two reviewers independently assign high/medium/low; resolve disagreement on high items. Adoption requires every high item verified directly against a primary source, all answer facts reviewed, and no unexplained mismatch. Reprioritize any missed critical claim before handoff.

## 6. Risks

Subjective risk ranking can bias attention. Low-priority facts remain rubric-bearing and must not be skipped.

## 7. Combines with

Strategies 2, 10, 24 and 30; schedule triage early, then complete full review.

## 8. Results log

NOT RUN. No fact-risk ranking or verification queue has been created.
