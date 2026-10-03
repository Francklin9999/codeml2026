# NOVA · Strategy 39: Documented versus recommended action language audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (commitment accuracy) |
| **Effort** | 2–3 h |
| **Depends on** | action register and brief text |
| **Rubric lines** | actions; post-event update |
| **Work folder** | work/strat39/ |

## 1. Context and evidence

The challenge explicitly requires distinguishing a documented commitment from the team's recommendation, and the live event must not invent approvals. Strategy 9 encodes this distinction in an action register. This proposal scans the prose views, where labels can be lost during summarization.

## 2. Idea and novelty

Maintain a controlled verb set for status statements—approved, proposed, assigned, recommended, planned, validated—and require every action sentence to map to a sourced fact or recommendation record. Unlike strategy 4's lifecycle states, this audits wording consistency in the final human-readable deliverable.

## 3. Rubric

Prevents a suggestion from becoming a false owner commitment through concise phrasing or UI labels.

## 4. Implementation

Create `work/strat39/language_audit.csv` with sentence, verb/status class, supporting fact ID, owner evidence, and reviewer. Scan brief, actions, answers, event update and presentation script.

## 5. Experiment and decision

Baseline: all imperative/action sentences in the rendered export. Require two reviewers and 100% of “approved/assigned/validated” assertions to have direct evidence; recommendations must be explicitly tagged. Any unsupported commitment blocks publication until corrected.

## 6. Risks

Keyword checks miss implied commitment and French inflection. Human review remains necessary, particularly after event integration.

## 7. Combines with

Strategies 4, 9, 14, 23, 25; run after final copy edits and again after the live event.

## 8. Results log

NOT RUN. No language scan or action-commitment review has been completed.
