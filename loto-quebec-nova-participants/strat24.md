# NOVA · Strategy 24: Citation confidence and source-quality rubric

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (audit precision) |
| **Effort** | 3 h |
| **Depends on** | extracted corpus and citations |
| **Rubric lines** | evidence; contradictions |
| **Work folder** | work/strat24/ |

## 1. Context and evidence

The corpus intentionally contains stale plans and a risk register, plus authoritative meeting records and tickets. Strategy 3 resolves claims using authority and time; this idea evaluates whether citations genuinely support the exact wording, not only whether a file exists.

## 2. Idea and novelty

Score each citation on directness, authority, temporal relevance, locator precision, and whether its quote entails the answer. Require a primary source for critical decisions or two independent sources when no single source is decisive. Unlike strategy 11's quote-presence check, this is semantic entailment review with explicit human adjudication.

## 3. Rubric

Strong citations reduce the chance that a technically valid locator is used to support a claim it does not establish.

## 4. Implementation

Create `work/strat24/citation_review.csv`; reviewers independently assess all answer citations using a fixed 0–2 scale and disagreement field. Quotes remain short and verbatim; notes separate interpretation from documented fact.

## 5. Experiment and decision

Baseline: all citations in Q01–Q10. Require two independent reviews for each answer and agreement within one point on every dimension; adjudicate disagreements. Proposed adoption threshold: no critical decision supported solely by low-authority or stale evidence; revise every claim scoring below 7/10 total.

## 6. Risks

Scoring can give subjective judgments a false numerical precision. Authority depends on corpus context and must be documented.

## 7. Combines with

Strategies 2, 3, 7, 10 and 11; do not use automated semantic similarity as a substitute for reviewer judgment.

## 8. Results log

NOT RUN. No citation entailment or quality review has been completed.
