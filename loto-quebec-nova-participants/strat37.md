# NOVA · Strategy 37: Contradiction impact tiers and escalation boundary

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (review routing) |
| **Effort** | 2–3 h |
| **Depends on** | verified contradiction register |
| **Rubric lines** | chronology; remaining actions |
| **Work folder** | work/strat37/ |

## 1. Context and evidence

The challenge requires explaining contradictions, but not every difference has the same operational consequence. Strategy 3 resolves conflicts, strategy 17 rebuilds risks, and strategy 19 records unknowns. This idea determines which unresolved conflicts must be surfaced as immediate takeover questions.

## 2. Idea and novelty

Assign each contradiction an impact tier based on whether it affects go-live authorization, budget, security/accessibility condition, or historical context; record who can resolve it only when the corpus supports that person. Unlike a risk register, this classifies evidence conflict and routes review rather than estimating probability.

## 3. Rubric

Helps an incoming owner focus on material discrepancies while keeping low-impact historical differences visible.

## 4. Implementation

Create `work/strat37/contradiction_triage.csv`; fields include both claims, current-state resolution, impact, evidence, confidence, and next question. Use qualitative tiers and document the rule before scoring.

## 5. Experiment and decision

Baseline: contradiction list from source review. Two reviewers independently tier all conflicts. Require 100% agreement on high-impact conflicts after adjudication and no “resolved” item without a source rationale. Use as a release view if the question owner and next step are clear or explicitly unknown.

## 6. Risks

Impact categories are team judgment and may not match sponsor priorities. Do not assign a named owner by inference.

## 7. Combines with

Strategies 3, 17, 19, 22 and 28; feed high-tier items into the handoff brief.

## 8. Results log

NOT RUN. No contradictions have been tiered under this method.
