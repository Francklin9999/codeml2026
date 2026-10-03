# Evidence available for strategies 21–40

**Cutoff: 2026-10-03.** This covers the five existing strategy series: NOVA, IVADO/EquiAlgo, DayOne, OptiFrame and Propolys. Their original hundred strategies have **not** all been implemented or tested. New ideas are proposals; an adoption threshold is a planned decision rule, never an observed result.

## What has actually been tested

| Challenge | Implemented/tested components | Evidence | Missing evidence |
|---|---|---|---|
| NOVA | Extractor ran; parent verified source/index/attachment hashes, 1,045 unique locators and all eight screenshot transcriptions; four audit tests | [Extraction audit](loto-quebec-nova-participants/work/strat1/report.md), [analysis](ANALYSE_CHALLENGES.md) | No full semantic locator/claim validation, completed ledger/site, blind answer grading or live event trial |
| IVADO / EquiAlgo | V1–V5 counterfactual candidates, nine reference simulations, budget validator, scorer | [Model results](equialgo-participants/work/strat1/report_01.md), [simulation assumptions](equialgo-participants/work/shared/README.md) | Hidden reference labels, official accuracy/score, 25-refit stability study, completed registry and H6 |
| DayOne | Provisional clinical schema and field/status evaluator; ten tests | [Audit report](dayone-participants/work/shared/report.md), [limits](dayone-participants/work/shared/README.md) | Reviewed page zones, specimen/phone-photo ground truth, OCR accuracy, multilingual review and offline workflow |
| OptiFrame | Board generation, homography, classical rim measurement, synthetic suite and connected frame STL; twelve tests | [Metrology](optiframe-participants/work/strat2/report.md), [frame audit](optiframe-participants/work/strat9/report.md) | Physical print scale/lens accuracy, camera distortion, anatomical orientation, phone UI, slicer/printing/fit |
| Propolys | Concept documents only | Existing `propolys-participants/strat1.md`–`strat20.md` | No completed interview, market comparison, demo evaluation, rehearsal or buyer validation |

The integrated focused suites now contain **78 passing tests**: 19 IVADO, 31 DayOne/OptiFrame, 24 bounded evidence-prototype tests and four NOVA extraction-audit tests. This does not mean all strategies have been implemented or their full adoption experiments passed. The OptiFrame synthetic experiment and EquiAlgo candidate generation are additional checks; passing those does not establish success for unimplemented strategies.

## New bounded experiments and parent audit

| Challenge | New measured result | Reproduction and limits |
|---|---|---|
| IVADO | Nine additional validated candidates from fixed-noise sensitivity, Student-t links, within-region pairwise ranking and income functional forms; all 4,000 rows / 1,600 grants | [Commands and audit](equialgo-participants/work/EXPERIMENTS.md), [20-row matrix](equialgo-participants/work/STRATEGY_TEST_MATRIX_21_40.md). Historical committee diagnostics only; no official upload. The df=10 t-link duplicates V1's decisions. |
| OptiFrame | Development-selected simplification: four radial-contour holdouts have max Hausdorff 0.04824 mm and 83.85–84.38% vertex reduction. Fixed scaling inconsistency: max normalized bounds drift 3.82e-6 mm across three scales | [Commands and audit](optiframe-participants/work/EXPERIMENTS.md), [matrix](optiframe-participants/work/STRATEGY_TEST_MATRIX_21_40.md). Simplification-only; total offset/STL error, full eye orientation, physical accuracy and fit unvalidated. |
| DayOne | Confirmed 124 PNGs, 80 unique hashes and 44 copies. Automatic group fingerprints link only 38/80 pages; no verified split is emitted | [Matrix](dayone-participants/work/STRATEGY_TEST_MATRIX_21_40.md). No reviewed identity mapping, perceptual duplicate review, ground truth or OCR accuracy. |
| NOVA | 64 sources match ZIP/index hashes; 1,045 unique locators; eight manually viewed/transcribed screenshots. Bundle, timestamp and alias prototypes have synthetic tests | [Extraction report](loto-quebec-nova-participants/work/strat1/report.md), [prototype scope](loto-quebec-nova-participants/work/EXPERIMENTS.md), [matrix](loto-quebec-nova-participants/work/STRATEGY_TEST_MATRIX_21_40.md). No validated factual ledger, final memory or event trial. |
| Propolys | Synthetic restore-record and custody-manifest checks, including path/type/chronology/hash controls | [Matrix](propolys-participants/work/STRATEGY_TEST_MATRIX_21_40.md). Hashes establish consistency, not authenticity; no AI workflow, buyer validation, restoration or legal/security certification. |

All three experimental branches were reviewed and integrated into `codex/strategies-21-40`. Parent fixes include fractional-label truncation, double income scaling, the wrong pair-count report, unsupported patient grouping, fixed-size frame overlap margins, unsafe HTML reads and unresolved alias collisions. Regenerable candidate CSVs are available locally under `equialgo-participants/work/_local/strat21`, `strat28`, `strat29` and `strat30`; collaborators reproduce them using the published runners rather than downloading committed generated data.

## IVADO: distinguish four different measurements

**Required target from the user: beat the current reported 94% leaderboard accuracy against the hidden reference.** The user confirmed the metric; the leaderboard entry and detailed evaluation protocol have not been independently checked. Final adoption must exceed 94% on that official accuracy metric while respecting the 36–44% grant constraint. A committee AUC, hypothetical-reference score or changed test split cannot establish this. The user can upload candidate files and return authorized aggregate feedback; no hidden labels are available.

First upload candidate: `equialgo-participants/work/_local/strat1/candidate_predictions_V1.csv`. The parent revalidated its 4,000 ordered candidate IDs, binary decisions and 1,600 grants (40%). It is a neutralized logistic baseline, not a verified >94% submission. Its official accuracy and F1 are pending. Generated candidate files remain git-ignored; reproduce them with `work/strat1/neutralise.py`.

1. **Committee prediction:** the label is what the historical committee decided. Five-fold AUC is approximately 0.957 for the logistic variants. This is AUC, not 95.7% accuracy. Selected regularization reused the tuning folds, so it is not independent model selection evidence.
2. **Fairness-corrected allocation:** all five candidate files give exactly 1,600 grants among 4,000 candidates. That satisfies the known budget constraint; it does not validate merit or equity against the hidden reference.
3. **Simulated scores:** nine hypothetical references are available. V1 and H1, and V4 and H5, share model families and can agree by construction. A perfect H1 score cannot establish jury accuracy. The hidden construction and exact agreement scoring remain unknown.
4. **Stability and conditional parity:** the measured five-refit pairwise Jaccard means are 0.982/0.979/0.982/0.917/0.982 for V1–V5. V4 misses the proposed 0.95 stability target despite its smaller academic-decile selection gap. The mean absolute remote/central decile gaps are 0.048/0.039/0.048/0.018/0.047. These are exploratory selection-rate comparisons, not equal-opportunity estimates against deserving applicants.

### Additional committee holdout check

After the initial reports, the parent measured a stratified 70/30 split with seed 42. Each model was refitted on the 7,000 training rows with its regularization selection inside that training subset. The following values are measured on 3,000 excluded rows:

| Variant | Raw committee accuracy (threshold 0.5) | Raw committee AUC | Corrected allocation agreement with committee (top 40%) |
|---|---:|---:|---:|
| V1 | 88.67% | 0.9544 | 86.27% |
| V2 | 88.67% | 0.9542 | 86.27% |
| V3 | 88.53% | 0.9542 | 86.33% |
| V4 | 88.10% | 0.9511 | 87.27% |
| V5 | 88.70% | 0.9545 | 86.33% |

This is a **post-hoc development holdout**, not a sealed test: earlier feature/method design already used the supplied historical data. Lower agreement after correction can be an intended consequence of changing biased decisions. Official accuracy against the 4,000-applicant hidden reference is **unknown**.

Reproduce with the repository environment:

```python
import sys
from pathlib import Path
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path("equialgo-participants/work").resolve()))
from shared import data, models

history = data.load_history()
train, test = train_test_split(history, test_size=0.3, random_state=42,
                              stratify=history[data.TARGET_COL])
for variant in models.VARIANTS:
    model, columns, details = models.fit_variant(train, variant, seed=42)
    raw = models.variant_scores(model, columns, test, train, variant, neutral=False)
    adjusted = models.variant_scores(model, columns, test, train, variant, neutral=True)
    prediction = data.top_k_mask(adjusted, round(len(test) * 0.4), test.cote_r_equivalent)
    print(variant, accuracy_score(test[data.TARGET_COL], raw >= 0.5),
          roc_auc_score(test[data.TARGET_COL], raw),
          accuracy_score(test[data.TARGET_COL], prediction))
```

## OptiFrame: promising simulation, unverified hardware

The fixed development suite has 15 cases: twelve zero-height lenses, one raised lens and two expected rejections. Combined A/B MAE is **0.080234 mm** on the twelve zero-height lenses; maximum absolute error is **0.312796 mm**. There are no unexpected failures or acceptances. Real refraction, glare and camera distortion are not modelled. This suite was used during development and is not an independent physical benchmark.

The 3 mm raised-lens simulation has A/B errors of +0.440025/+0.369844 mm before a correction supplied with known height/distance/nadir, and +0.020475/+0.063320 mm afterward. This supports checking height bias; it does not validate automatic pose/height estimation or oblique-camera correction.

A frame generated from two actual measurement JSONs from simulated images passed watertightness, winding, positive volume, connected-body and nondegenerate-face checks. Audit found and fixed board-coordinate alignment, bridge obstruction, swallowed tenons and CLI error handling. Mesh validity is not a physical fit or strength measurement.

## DayOne: evaluation integrity before extraction claims

The ten tests exercise missing fields, status confusion, hallucination, aliases, strict numerical/unit comparison, duplicate pages/keys, privacy-key checks, calibration and date handling. No field-level OCR accuracy has been measured. The provisional schema has not been reviewed against specimen zones. Key-based privacy checks do not detect personal data embedded in allowed free-text values, and random-looking patient codes do not prove anonymisation.

New experiments should give independently reviewed labels, explicit unit/date contracts and defensible patient/page splits before claiming an extraction improvement.

## NOVA and Propolys: no completed experiments to extrapolate from

NOVA's analysis and draft factual answers can anchor corpus-specific experiments. They do not establish search, evidence navigation or post-event update performance. Propolys has no measured demand or pitch results. A proposed buyer, price or interview threshold is a hypothesis to test.

## How the new ideas are selected

Prefer ideas that resolve an evidenced failure or a required missing deliverable. Each strategy must identify its nearest existing strategy and state a concrete difference in mechanism, evaluation design or workflow. Repeating an old method under a new name does not count. Planned baselines, holdouts, numerical adoption/kill gates and prerequisites should make the idea testable; avoid invented expected jury scores or observed gains.

Primary technical guidance consulted during drafting: [OpenCV ChArUco detection](https://docs.opencv.org/5.0/tutorials/objdetect/charuco_detection/charuco_detection.html), [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), and [CISA product security guidance](https://www.cisa.gov/news-events/alerts/2025/01/17/cisa-and-fbi-release-updated-guidance-product-security-bad-practices). These provide method/governance context, not validation of our prototypes or proof of buyer demand.
