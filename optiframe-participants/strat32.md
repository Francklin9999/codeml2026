# OptiFrame · Strategy 32: Mobile interaction performance budget

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 10 browser app prototype |
| **Work folder** | `optiframe-participants/work/strat32/` |

## 1. Context and evidence

No mobile app or phone tests are reported. Strategy 10 plans a web app and strategy 19 a server fallback, with existing 30-second pair budget; strategy 9's browser generation target is untested. This proposal profiles user-visible stage latency and memory on constrained mobile hardware once a prototype exists, rather than selecting a deployment architecture.

Evidence: [CONTINUATION.md](../CONTINUATION.md) records browser and phone integration as unfinished.

## 2. Idea and distinction

Break the interaction into camera permission, capture, board detection, measurement, preview, and STL export. Measure cold/warm latency, peak memory, and cancellation responsiveness separately. Set budgets per stage and show a friendly progress state when exceeded. Test offline startup separately from computation.

## 3. Rubric relevance

Supports the mobile-app and performance portions of the rubric and prevents one slow stage from making the demo appear frozen.

## 4. Implementation steps

Add `work/strat32/perf_harness.js`, synthetic fixtures, and a device matrix. Record browser/OS/device class and keep raw camera frames local. Include a low-memory failure path and cancellation test.

## 5. Proposed experiment

On two available phones, run 10 warm and 5 cold repetitions of a synthetic measurement and frame generation. Baseline: current desktop Python pipeline (document as non-comparable). Proposed adopt criteria: p95 full flow <10 s, STL export <5 s, no tab reload, peak memory <300 MB; revise only after measurement. These are targets, not results.

## 6. Risks

Two devices cannot represent browser diversity; keep a graceful supported-device fallback.

## 7. Combinations

Pairs with strategies 9, 10, 19, 27, and 30.

## 8. Results log

NOT RUN. No browser or phone integration has been tested.
