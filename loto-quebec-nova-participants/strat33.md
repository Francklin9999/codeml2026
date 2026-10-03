# NOVA · Strategy 33: Audience-specific handoff path without duplicate facts

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (takeover usability) |
| **Effort** | 3–4 h |
| **Depends on** | fact ledger and user roles |
| **Rubric lines** | one-page brief; use & uncertainty |
| **Work folder** | work/strat33/ |

## 1. Context and evidence

The challenge asks for a useful operational memory for someone taking over NOVA. Strategy 14 maps RACI, and strategy 9 creates a brief plus action register. Different handoff roles need different starting points, but duplicated fact text can drift.

## 2. Idea and novelty

Offer role-based navigation entry points (project manager, security lead, finance reviewer) that filter the same sourced records, never author independent copies of facts. This differs from a stakeholder accountability matrix: it changes the reader's route through the memory while retaining a single source of truth.

## 3. Rubric

Readers can quickly find their relevant actions while the evidence, status labels, and source links stay consistent.

## 4. Implementation

Create `work/strat33/role_views.md` and add role tags to fact/action IDs only where supported. Each view links to shared records and states that role assignments not documented are proposed rather than confirmed.

## 5. Experiment and decision

Baseline: general navigation and action register. Give three cold readers different role cards and ask them to identify current status, next action, evidence, and unknown. Adopt if 3/3 find the right sourced record within 2 minutes and none mistakes a proposal for commitment.

## 6. Risks

The corpus may not establish actual role boundaries; role segmentation can imply unsupported responsibility. Keep role names generic unless sourced.

## 7. Combines with

Strategies 9, 14, 21 and 33; derive all views from common fact IDs.

## 8. Results log

NOT RUN. No role-specific navigation or cold-reader test exists.
