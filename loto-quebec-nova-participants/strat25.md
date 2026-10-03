# NOVA · Strategy 25: Answer dependency graph and single-change regression

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (consistency after edits) |
| **Effort** | 3–4 h |
| **Depends on** | answer facts and generated views |
| **Rubric lines** | factual accuracy; chronology; update |
| **Work folder** | work/strat25/ |

## 1. Context and evidence

One source may support several answers or brief sections; an update to a go-live date or owner can leave duplicated text stale. Strategy 5 freezes state and strategy 23 maps event impacts. This proposal tests whether edits propagate consistently through all published outputs.

## 2. Idea and novelty

Build a dependency graph from source locator to fact ID to answer/action/brief sentence, then mutate one fact in a temporary fixture and assert every dependent rendering changes while unrelated output stays identical. Unlike strategy 23's live-event impact mapping, this is automated regression coverage for ordinary editorial changes.

## 3. Rubric

Prevents contradictory dates or owners from appearing in different parts of the operational memory.

## 4. Implementation

Create `work/strat25/dependencies.json` and a renderer test. Every generated sentence carries hidden provenance IDs or an adjacent fact-ID field; test fixtures contain fabricated values and never modify corpus records.

## 5. Experiment and decision

Baseline: generated answers, brief, action register and timeline. Test 10 single-fact substitutions. Adopt if all intended dependent views update and all unrelated views remain byte-identical; any missed or spurious change blocks release. Keep fixtures explicitly marked synthetic.

## 6. Risks

Hand-authored prose may bypass the graph. Tests can confirm linkage, not truth of changed data.

## 7. Combines with

Strategies 1, 5, 9, 23; run as release gate after each real event update.

## 8. Results log

NOT RUN. No graph, mutation fixture, or regression result exists.
