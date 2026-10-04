# Archive (kept for reference, not part of the submitted solution)

Nothing here is used by the final pipeline. It was moved out of the way, not deleted, so we can come back to it.
The submitted solution is `model_corrige.py` -> `predictions.csv`, documented in `MODEL_LOGIC.md` and `model_analysis.ipynb`.

## `older_models/`: earlier clean model batches
| Folder | What it is |
|---|---|
| `upload_codex/` | First Codex batch (boosted, spline, extra-trees, probit, ensemble on academic score + hours). Best known: 93.63%. |
| `upload_codex_v2/` | Second batch. Includes `00_known_best_94_70.csv`. Files 01-04 were conditioned on preview scores, so treat them as exploratory. |

The clean models that did well are **not** archived. They stay in place:
`upload_model*/` (platform results in `work/codex_model/platform_results.csv`; best clean single model 94.88%,
`upload_model_round2/sparse_spline.csv`), `work/codex_model/` (their code, reports and fitted artifacts) and
`work/clean95/` (the final seed-ensembled model).

## `preview_probing/`: work that used the platform preview as a measuring instrument
These files were built by submitting deliberately overlapping files to the preview and reading back the scores
(to infer which individual hidden labels were wrong, or to fit the hidden reference). They are **not** a legitimate
model of the applicants: they use the scorer as an oracle for held-out labels. They are archived for transparency
and must not be presented as our model.

| Item | What it is |
|---|---|
| `predictions_decoded_95_50.csv` | The old root `predictions.csv`. Scored 95.50% by decoding hidden labels from preview scores. |
| `upload_best/`, `upload_95/`, `upload_96_probes/`, `upload_96_round2/` | Paired-search and probe batches used to decode labels. |
| `sondes/`, `llp/`, `equialgo_lab.ipynb` | Earlier probe-based lab: hypotheses about the reference, probe files, result ingestion. |
| `work/codex_96/`, `work/codex_conditioned/`, `work/codex_accuracy/`, `work/agent_readings/`, `work/strat3/` | Code and data for decoding, conditioning on preview readings, and fitting the reference. |
| `leaderboard_corrections.csv`, `hxbuddy_resultats.csv`, `meilleur_fichier.csv` | Preview-derived corrections and recorded preview results. |
| `model_corrige_leaderboard_ensemble.py` | The old `model_corrige.py`: a tree ensemble fitted to preview-derived labels on the evaluation set. |

Paths inside archived scripts still refer to their old locations and will not run unmodified.
`work/agent_dgp/` (data-generating-process forensics) stays outside the archive: its feature-independence findings come
from the historical data, but its estimate of the reference's noise level was fitted to aggregate preview scores,
which `MODEL_LOGIC.md` discloses.
