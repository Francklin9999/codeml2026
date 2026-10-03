# Claude Desktop continuation — recovered 2026-10-03

## Where the local work was found

Claude Desktop's Claude Code transcript is under:

```text
C:\Users\franc\.claude\projects\C--Users-franc-AppData-Roaming-Claude-scratch-workspaces-cb8af308-9bf9-49a1-ac12-cb94a3cafff3-6b722c36-a060-419b-9cae-d13a10146158-scratch-2026-10-03-b03b09\29df5b52-ff16-4312-b3f3-ce5d0adf0960.jsonl
```

The related session directory contains `subagents/agent-*.jsonl` transcripts. Windows tools can fail to enumerate those long paths even when the top-level transcript is readable. No transcript or unrelated private conversation was copied into this repository.

The durable implementation plans are already in the repo: `ANALYSE_CHALLENGES.md` and twenty `stratN.md` files in each of the five challenge folders. Claude's latest session planned foundation-first experiments followed by the remaining strategies. It reached its usage limit around 18:10 UTC on October 3, and the background tasks reported API-limit failures. The strategy statuses had not been updated.

## What existed before this continuation

- NOVA: `work/strat1/nova_common.py` and `extract.py`.
- EquiAlgo: `work/shared/data.py`.
- DayOne: `work/strat1/pdfparse.py`.
- OptiFrame: strategy notes, no implementation files.
- Propolys: strategy notes; no completed experiment reports found in the repository.

Those existing files were preserved. The only modified existing implementation is EquiAlgo's `data.py`, which now rejects invalid top-k inputs and nonbinary submission values instead of silently truncating them.

## Work completed in this continuation

The user selected **DayOne or OptiFrame** as the priority; the implementation proceeded with OptiFrame.

- **OptiFrame strategies 1–3:** runnable local board generation, synthetic-image generator, metric rectification, classical rim detector, sub-pixel edge refinement, dimension/perimeter measurement, optional fronto-parallel height correction, JSON/SVG/debug exports, print-scale checker, tests and reports. Read `optiframe-participants/work/README.md` for commands. Fifteen synthetic cases pass with zero unexpected acceptance/rejection; the twelve zero-height cases have combined A/B MAE 0.080234 mm and maximum error 0.312796 mm. Six tests pass. Physical tests remain NOT RUN.
- **EquiAlgo strategy 2:** shared validator/scorer and nine hypothetical references implemented, six tests and a data smoke run pass. Read `equialgo-participants/work/shared/README.md` for remaining work and simulation assumptions.

All regenerable photos, PDFs, masks, extracted outputs and smoke fixtures remain under git-ignored `_local/` folders. No new dependencies were installed, and no commits or remote pushes were made during this continuation.

## Next concrete work

1. OptiFrame: collect independent real-lens and printed-shape measurements using `work/strat1/rig_instructions.md`; finish canonical orientation (strategy 8), connected grooved frame/STL generation (9), then phone UI (10).
2. DayOne: resume `pdfparse.py` with schema, per-page zone templates, reviewed ground truth and field-level evaluation (strategy 1). Do not treat PDF text-layer extraction as a working phone OCR system.
3. NOVA: run/review the extractor, add screenshot transcriptions, then curate the evidence ledger and build/check the static site (strategy 1).
4. EquiAlgo: add the model runner, stability/conditional-parity reports and registry; complete the robustness matrix and calibration investigation. H6 remains unimplemented because the latent reference generator is unidentified.
5. Propolys and other strategies: still unimplemented unless individually logged otherwise. The original hundred-strategy campaign is **not complete**.

Keep source datasets untouched, report simulations as simulations, and update each strategy's status/results log only after its stated tests run. The original confidentiality exclusions in `.gitignore` remain in force.
