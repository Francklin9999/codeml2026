# OptiFrame · Strategy 30: Result package reproducibility bundle

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 CLI and strategy 9 STL exporter |
| **Work folder** | `optiframe-participants/work/strat30/` |

## 1. Context and evidence

The strategy-2 report records synthetic metrics and a reproducible command; strategy 9 records a mesh smoke test, but its inputs are also synthetic. Physical tests are unrun. This proposal captures enough non-sensitive configuration to reproduce a particular generated output locally, rather than improving measurement, exporting another file format, or adding browser/server deployment.

Evidence: [metrology report](work/strat2/report.md) and [STL audit](work/strat9/report.md) contain synthetic reports, not physical validation.

## 2. Idea and distinction

Package a run manifest with input image hash, board definition, algorithm version, parameters, unit convention, environment versions, output hashes, and all warnings. Add a deterministic replay command and compare the replayed JSON/SVG/STL summaries to the manifest. Raw images remain local and excluded from shared bundles unless explicitly synthetic.

## 3. Rubric relevance

Supports code quality, reviewability, and honest presentation by linking claims to a precise run configuration.

## 4. Implementation steps

Implement `work/strat30/run_bundle.py` and manifest schema. Ensure the bundle does not copy private photos by default; include fixture ID and hash only. Record OpenCV, NumPy, and mesh-library versions.

## 5. Proposed experiment

Recreate 15 existing synthetic pipeline cases from their manifests, baseline current ad hoc command outputs. Adopt if all dimension values match to 1e-6 mm in the same environment, mesh topology counts are stable, and input images are not duplicated into the bundle; kill if runtime metadata cannot reproduce divergent outputs. Proposed criteria, not measured.

## 6. Risks

Library versions can change floating-point and mesh ordering; compare geometry metrics when byte hashes are unstable.

## 7. Combinations

Pairs with strategies 2, 9, 10, 21, 26, and 27.

## 8. Results log

NOT RUN. Existing reports include commands and summaries, not portable run manifests.
