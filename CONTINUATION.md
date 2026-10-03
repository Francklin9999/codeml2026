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

- **OptiFrame strategies 1–3 and 9:** runnable board generation, synthetic-image generator, metric rectification, classical rim detector, sub-pixel edge refinement, dimension/perimeter measurement, optional fronto-parallel height correction, JSON/SVG/debug exports, print-scale checker and connected grooved frame STL generation. Read `optiframe-participants/work/README.md` for commands. Fifteen synthetic cases pass with zero unexpected acceptance/rejection; the twelve zero-height cases have combined A/B MAE 0.080234 mm and maximum error 0.312796 mm. Six metrology and six frame tests pass. A frame from two actual pipeline outputs passed all five mesh validity gates. Physical tests remain NOT RUN.
- **DayOne strategy 1, partial:** provisional clinical schema and evaluator implemented; ten tests pass. No reviewed zones or ground-truth pages were created. Read `dayone-participants/work/shared/README.md`.
- **EquiAlgo strategies 1–2:** shared validator/scorer, nine hypothetical references and V1–V5 model runner implemented; six scorer tests pass. The parent independently reproduced all five 1,600-grant candidates. Read `equialgo-participants/work/strat1/report_01.md` for measured diagnostics and `work/shared/README.md` for simulation assumptions. V4 misses the planned stability threshold; no official submission is selected.

All regenerable photos, PDFs, masks, candidate files and smoke fixtures remain under git-ignored `_local/` folders; small measured Markdown reports are versioned. No new dependencies were installed.

## Subagent audit and Git checkpoints

At the user's request, three `gpt-6-luna` agents with low reasoning effort and no inherited conversation worked on bounded tasks in isolated `.worktrees/` directories. The parent reviewed each source diff, requested fixes, independently ran checks, then committed and pushed the batches:

| Branch | Reviewed checkpoint | Contents |
|---|---|---|
| `codex/claude-recovery` | `060e3b6` foundation; subsequent integration commits | Preserved Claude starter files, tested metrology and integrated audited batches |
| `codex/equialgo-models` | `9e964c5` | Model runner, validated candidates, conditional parity/stability report |
| `codex/dayone-evaluation` | `b9056d3` | Schema, evaluator, regression tests and limits |
| `codex/optiframe-frame` | `2d70776` | Layered frame STL, bridge/tenons, geometric tests and report |

Audit fixes include off-centre measured contours, a bridge obstructing lens seats, swallowed tenons, bogus CLI exception handling, duplicate page/key matching, numerical unit parsing, future short-year dates and tolerance boundaries. Twenty-eight focused tests pass across the four suites. `codex/claude-recovery` integrates the three feature branches; `main` is unchanged.

## Next concrete work

1. OptiFrame: collect independent real-lens and printed-shape measurements using `work/strat1/rig_instructions.md`; finish canonical orientation (strategy 8), validate frame printing/fit and implement browser integration (9–10).
2. DayOne: connect `pdfparse.py` to the provisional schema, per-page zone templates, reviewed ground truth and the implemented evaluator (strategy 1). Do not treat PDF text-layer extraction as a working phone OCR system.
3. NOVA: run/review the extractor, add screenshot transcriptions, then curate the evidence ledger and build/check the static site (strategy 1).
4. EquiAlgo: extend stability to the planned seed/refit sweep, add the registry and complete the robustness matrix/calibration investigation. H6 remains unimplemented because the latent reference generator is unidentified.
5. Propolys and other strategies: still unimplemented unless individually logged otherwise. The original hundred-strategy campaign is **not complete**.

Keep source datasets untouched, report simulations as simulations, and update each strategy's status/results log only after its stated tests run. The original confidentiality exclusions in `.gitignore` remain in force.
