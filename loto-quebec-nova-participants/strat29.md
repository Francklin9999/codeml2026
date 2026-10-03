# NOVA · Strategy 29: Critical-path evidence graph for go-live conditions

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (operational handoff) |
| **Effort** | 4 h |
| **Depends on** | verified go-live conditions and action register |
| **Rubric lines** | brief & actions; current state |
| **Work folder** | work/strat29/ |

## 1. Context and evidence

The brief requires linking three go-live conditions to actions, owners, and due dates where known. The supplied analysis says the 22 October date is conditional, but there is no completed ledger or verified action graph. This idea examines dependency and evidence without inventing schedule commitments.

## 2. Idea and novelty

Model each documented go-live condition as a gate connected to evidence, owner, predecessor, and consequence if unresolved. Mark unsupported dependencies and dates as unknown. Unlike strategy 9's flat action register and strategy 17's risk register, this focuses on the logical chain showing why each condition gates go-live.

## 3. Rubric

The handoff communicates operational dependencies and avoids treating a date as an unconditional authorization.

## 4. Implementation

Create `work/strat29/gates.yaml` and render a dependency diagram. Each edge cites a locator; proposed actions and owners carry explicit “recommendation” labels. Cross-check the graph against contract/change records and latest primary sources.

## 5. Experiment and decision

Baseline: three documented conditions after source verification. Require every gate and edge to trace to a source or be labeled as team inference. Cold operator should identify the three unresolved gates and next action in under 2 minutes; block use if any recommendation appears as a commitment.

## 6. Risks

The source set may not define dependencies or owners. A graph can overstate precision and imply a schedule that was never approved.

## 7. Combines with

Strategies 9, 14, 17, 22; keep risk likelihood and project gating distinct.

## 8. Results log

NOT RUN. No condition dependency graph or operator test exists.
