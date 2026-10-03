# OptiFrame · Strategy 26: Geometric failure taxonomy and fault injection

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 2 CLI and synthetic generator |
| **Work folder** | `optiframe-participants/work/strat26/` |

## 1. Context and evidence

Fifteen synthetic cases currently have zero unexpected acceptance/rejection, and the test suite checks missing markers and empty windows. Physical cases remain untested. Existing strategies address robustness, multishot consistency, and exposure quality. This proposal systematically probes malformed inputs and numerical boundary conditions in the pipeline contract, rather than expanding optical coverage.

Evidence: [metrology report](work/strat2/report.md) lists 15 synthetic cases and focused input checks.

## 2. Idea and distinction

Build a fault-injection catalog for NaNs, extreme resolutions, clipped board corners, duplicated marker IDs, almost-empty contours, self-intersections, unsupported image channels, and invalid JSON parameters. Require every input to either produce a valid result with diagnostics or fail with a stable actionable error; never emit plausible dimensions from invalid geometry.

## 3. Rubric relevance

Targets the robustness criterion’s “without crashing” requirement and improves demo predictability.

## 4. Implementation steps

Add `work/strat26/fault_cases/`, seeded mutations, and a compact error classification report. Run through the CLI and library entrypoints; preserve existing reference fixtures. Avoid broad redesign unless a reproduced failure demands it.

## 5. Proposed experiment

Run 100 deterministic malformed inputs, baseline existing 15-case acceptance suite. Adopt if all invalid cases fail safely, no unhandled exceptions occur, and valid outputs remain byte-for-byte unchanged; kill a fault family as non-actionable if it cannot be represented by supported input formats. Proposed thresholds, not measured.

## 6. Risks

Synthetic fault coverage is not physical robustness. Avoid overfitting public input validation to unrealistic cases.

## 7. Combinations

Complements strategies 2, 3, 7, 9, 10, and 21.

## 8. Results log

NOT RUN. Existing tests do not cover this proposed fault matrix.
