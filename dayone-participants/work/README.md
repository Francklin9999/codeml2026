# DayOne — engineering notes (extraction pipeline and strategy implementations)

> Product overview, quick start and demo: see [`../README.md`](../README.md), [`../DEMO.md`](../DEMO.md),
> [`../LIFECYCLE.md`](../LIFECYCLE.md). This file documents how each strategy was built and measured.

Everything here was built and tested on 2026-10-03 from the 20 strategy write-ups (`../strat1.md … strat20.md`),
then revised on 2026-10-04: recogniser v3, grammar-constrained decoding, visit-table rules, strict uncertainty
metrics, and the fixes of an independent audit (privacy of unrecognised pages, browser cache, HTTPS + pairing,
roles for the kept image, resumable lifecycle, sklearn-free calibrator).
The goal of this pass was **maximum field-level extraction accuracy** (rubric: 30 pts extraction + 20 pts
uncertainty), plus working, tested versions of the product strategies.

Results are in [`results.md`](results.md) (one line per evaluation run) and summarised in
[`RESULTS_SUMMARY.md`](RESULTS_SUMMARY.md).

## Pipeline (what runs on a photo)

```
photo ─► register (strat 2/4): page quad → page type (8 templates, twin-page check) → ECC homography
      ─► mask identifier zones (strat 10)                       ─► never read, never stored
      ─► crop every field zone (template geometry, strat 1/2)
      ─► CRNN-CTC recogniser (strat 11, trained on synthetic pages, strat 5)  [+ optional TTA]
      ─► constrained CTC rescoring: vocabularies FR/EN/AR, date / BP / number+unit grammars (strat 7/11);
         when the free reading is not a valid value, a grammar-constrained CTC beam search proposes the most
         likely valid ones (grammar_decode.py)
      ─► checkboxes: OMR CNN (strat 18)
      ─► booklet consistency rules + likelihood-checked repair (strat 7/13), incl. the visit table:
         appointment = visit + 28 d, fundal height = SA − 4
      ─► calibrated confidence + status CONNU / À_RÉVISER / ILLISIBLE / NON_FOURNI / INCONNU (strat 6)
      ─► review dialogue (strat 9) → lifecycle / encrypted store / outbox (strat 8) → linking (strat 10)
```

## Layout

| Folder | Strategy | Content |
|---|---|---|
| `shared/` | 1 | `common.py` paths/helpers, `eval.py` shared scorer, `gt/` exact ground truth (80 pages), `templates.json` zones |
| `strat1/` | 1 | `build_gt.py` GT from the PDF text layer + vector checkboxes; `overlay.py` visual check |
| `strat2/` | 2 | `templates.py` zones/blank forms, `register.py`, `crops.py`, `extract_zonal.py`, `run_eval.py`, `test_register.py` |
| `strat3/` | 3 | `vlm_extract.py` (Qwen2.5-VL-3B, local, 4-bit), `bench_vlm.py` |
| `strat4/` | 4 | `degrade.py` seeded phone-photo degradations with exact homography, `quality_gate.py` gate vs extraction outcomes, `gate_report.py` accuracy on gate-accepted photos |
| `strat5/` | 5 | `vocab.py` FR/EN/AR vocabularies + sampler + canonicaliser, `synth_pages.py` synthetic filled pages (Arabic shaped with HarfBuzz; optional irregular "writer" — slant, spacing, baseline wander, pen width, elastic — and handwriting-bank patches) |
| `strat6/` | 6 | `calibrate.py` signals → logistic calibrator (scribble-aware), `apply_cal.py` metrics on saved runs, `status_bench.py` per-status confusion matrix |
| `strat7/` | 7, 13 | `fieldlogic.py` grammars + CTC rescoring, `grammar_decode.py` grammar automata + constrained CTC beam search, `validator.py` cross-field / cross-page rules with repair, `replay_rules.py` rule ablation on saved readings, tests |
| `strat8/` | 8 | `offline.py` lifecycle state machine, AES-GCM store, idempotent outbox; property-based tests |
| `strat9/` | 9 | `dialogue.py` deterministic review flow FR/EN; golden-transcript tests |
| `strat10/` | 10 | `privacy_linking.py` leak scanner + code-based linking; tests |
| `strat11/` | 11 | `crnn.py`, `gen_dataset.py`, `pack.py`, `train_crnn.py`, `recognizer.py` |
| `strat12/` | 12 | `arbitrate.py` multi-engine arbitration |
| `strat16/` | 16 | `hitl.py` online recalibration simulation |
| `strat13/` | 13 | `reconcile.py` validated-record reconciliation + simulation test |
| `strat14/` | 14 | `whatsapp_adapter.py` Cloud API payloads + idempotent webhook (offline tests) |
| `strat15/` | 15 + 9 | `app/` the WhatsApp-style phone app (capture, quality gate, encrypted queue, review, manual entry, match, sync, re-scan diff, FR/EN), `gen_schema.py`, `app/testdata/e2e.js` automated rehearsal (`/?db=e2e&e2e=1`) |
| `strat17/` | 17 | `dedup.py` exact / near duplicates, re-scan diff; tests |
| `strat18/` | 18 | `omr.py` checkbox CNN, `eval_omr.py` |
| `strat19/` | 19 | `dashboard.py` anonymised aggregates (k=5 suppression, missing counts, optional DP noise) |
| `strat20/` | 20 | `edge_server.py` facility box: /process, /session/finalize, /match, /records, /dashboard; state encrypted at rest |
| `strat21/` | — | `gemini_handwriting.py` handwriting bank from an image model (needs an API key, not used for the results; only fictitious values leave the machine, enforced by a guard), offline tests — see `../AMELIORATIONS_EXTERNES.md` |

## Reproduce

Heavy artefacts (fonts, generated datasets, models, predictions) live outside OneDrive in
`%USERPROFILE%\dayone_local` (override with `DAYONE_LOCAL`). Python 3.13 venv with CUDA PyTorch:

```bash
python -m venv %USERPROFILE%\venvs\dayone
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install pymupdf opencv-python-headless numpy pandas pillow scikit-learn scipy pyyaml rapidfuzz fonttools arabic-reshaper python-bidi cryptography hypothesis pytest fastapi httpx python-multipart transformers accelerate bitsandbytes
```

```bash
python work/strat1/build_gt.py                 # GT (80 pages) + schema
python work/strat2/templates.py                # zones + blank templates
# fonts: 69 OFL Google fonts in dayone_local/fonts (see strat5/synth_pages.py)
python work/strat11/gen_dataset.py --pages 3500 --out ~/dayone_local/ds_v1 --holdout 1   # specimen fonts excluded
python work/strat11/gen_dataset.py --pages 3000 --out ~/dayone_local/ds_v2 --holdout 0 --seed 200000
python work/strat11/gen_dataset.py --pages 1500 --out ~/dayone_local/ds_cb2 --holdout 0 --seed 500000 --cb_only 1
python work/strat11/train_crnn.py --data ~/dayone_local/ds_v1 --out ~/dayone_local/models/crnn_v1.pt --epochs 6
python work/strat11/train_crnn.py --data ~/dayone_local/ds_v1 ~/dayone_local/ds_v2 --init crnn_v1_ep2.pt --epochs 2 --lr 6e-4 --bs 32 --out crnn_final.pt
# v3 (shipped): more degraded photos + irregular "writer" pages, fine-tuned from the previous model (~40 min)
python work/strat11/gen_dataset.py --pages 4000 --out ~/dayone_local/ds_v3 --holdout 0 --hw_aug 0.6 --seed 3000000 --sev_p 0.1 0.25 0.3 0.2 0.15
python work/strat11/train_crnn.py --data ~/dayone_local/ds_v1 ~/dayone_local/ds_v2 ~/dayone_local/ds_v3 --init crnn_final.pt --epochs 1 --bs 32 --lr 4e-4 --max_steps 14000 --out crnn_v3.pt
python work/strat11/export_model.py ~/dayone_local/models/crnn_v3.pt models/crnn_final.pt     # fp16, same alphabet
# honest variant: same recipe without the 5 specimen fonts, from the held-out lineage
python work/strat11/train_crnn.py --data ~/dayone_local/ds_v1 ~/dayone_local/ds_v2 ~/dayone_local/ds_v3 --exclude_fonts "Caveat[wght].ttf" ShadowsIntoLight.ttf NanumPenScript-Regular.ttf Gaegu-Regular.ttf ReenieBeanie.ttf --init crnn_v1_ep2.pt --epochs 1 --bs 32 --lr 4e-4 --max_steps 14000 --out crnn_v3_heldout.pt
python work/strat18/omr.py train --data ~/dayone_local/ds_v1 ~/dayone_local/ds_v2 ~/dayone_local/ds_cb2 --out omr_v2.pt
# calibrator: signals on synthetic pages (never the specimen) -> logistic, saved as JSON
python work/strat6/calibrate.py collect --model ~/dayone_local/models/crnn_v3.pt --omr models/omr_v2.pt --pages 160 --seed 5000 --out ~/dayone_local/cal_rows_v3.jsonl
python work/strat6/calibrate.py fit --rows ~/dayone_local/cal_rows_v3.jsonl --iso 0 --out models/calibrator.json
python work/strat2/run_eval.py --model models/crnn_final.pt --omr models/omr_v2.pt --cal models/calibrator.json --sev 0 1 2 3 4 --pages 1-80 --tag release3 --save_raw 1
python work/strat4/gate_report.py --tag release3 --sev 1 2 3 4      # accuracy on the photos the quality gate accepts
python work/strat7/replay_rules.py --raw ~/dayone_local/preds/release3_sev2_raw.pt --model models/crnn_final.pt   # rule ablation
pytest work
```

## Evaluation protocol (honesty notes)

* Test set = the 80 specimen pages (10 patients × 8 page types), exact GT from the PDF text layer.
  They are **never** used for training; synthetic training pages are generated from blank templates.
* "Held-out fonts" runs use a model trained without the 5 handwriting fonts of the specimen
  (Caveat, Shadows Into Light, Nanum Pen, Gaegu, Reenie Beanie): that is the generalisation to unseen handwriting.
* Vocabulary snapping uses **leave-one-patient-out** vocabularies during evaluation (values observed on
  the 9 other patients + generic FR/EN/AR lists), so free-text answers are not leaked.
* Degraded runs (severity 1–4) push the specimen PNGs through `strat4/degrade.py` (perspective, shadows,
  blur, noise, JPEG, low light, occlusion) and through the *full* pipeline (registration included).
* Score = canonical exact match per field (dates, numbers + units, enums mapped across FR/EN/AR).
