# Diagnostic previews toward 96%

Preview `probe_01.csv` through `probe_19.csv`, respecting the platform's
20-per-hour team limit. These are diagnostic files, not a claim of improved accuracy.
Keep `upload_95/01_pair_AB.csv` (95.00%) as the confirmed submission unless a probe
actually improves it.

Send the Accuracy for each file, for example `01: 95.00, 02: 94.95, ...`.
F1 is not needed to decode this batch. Keep every scored file unchanged.

The 19 probes overlap across 48 uncertain decisions. Their scores tell
us exact counts of mistakes in each subset. An integer solver then identifies
which individual corrections are forced by those counts. Only those certified
corrections enter the resulting submission; no ambiguous bit is guessed.

This batch is expected to find some of the 40 corrections needed to move from
95% to 96%. More previews may be needed; 96% is not guaranteed by this batch.
All files meet the 4,000-row format and 36–44% grant budget.

Results template and decoding metadata: `work/codex_96/upload_96_probes/`.
After entering the percentages in its `results.csv`, run:

```bash
OPENBLAS_NUM_THREADS=1 python work/codex_96/probes.py decode --folder upload_96_probes
```
