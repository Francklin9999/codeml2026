# DayOne — a midwife, a phone and an AI

An offline-first, WhatsApp-style agent that turns photos of the paper maternal registry into a structured,
verified, longitudinal record. The midwife keeps her paper registry; the phone reads it, **shows only what it is
unsure about**, keeps everything encrypted until the network returns, and links each visit to the right woman by
the code written on the registry — never by her name.

| | |
|---|---|
| Demo script | [`DEMO.md`](DEMO.md) (offline capture → connectivity back → review of an uncertain field → match decision) |
| Record lifecycle | [`LIFECYCLE.md`](LIFECYCLE.md) |
| Measured results | [`work/RESULTS_SUMMARY.md`](work/RESULTS_SUMMARY.md), every run in [`work/results.md`](work/results.md) |
| Engineering notes, per strategy | [`work/README.md`](work/README.md) and `strat1.md … strat20.md` (status + results log of each) |

## Quick start (≈ 5 min, no training needed)

```bash
pip install -r requirements.txt          # GPU optional: install torch from the CUDA index first for speed
./run_box.sh                             # Windows: .\run_box.ps1
# open http://localhost:8765 (or http://<box-ip>:8765 on a phone on the same Wi-Fi), PIN of your choice
pytest work                              # ≈ 30 tests: lifecycle/chaos, crypto, dialogue, linking, extraction
```

Trained models ship in `models/` (CRNN 13 MB fp16, checkbox CNN 0.3 MB, calibrator 2 KB). Page templates are
rebuilt from the specimen PDF automatically on first use. Re-training everything is documented in
`work/README.md` (synthetic data generation + ~1 h on a laptop GPU).

## Architecture

```
 phone (PWA, works offline)                       facility edge box (local Wi-Fi, no internet needed)
 ─────────────────────────────                    ───────────────────────────────────────────────────
 📷 capture + on-device quality gate     ──►      /process   register page → mask identifiers → read every field
 🔐 IndexedDB, AES-GCM (PIN-derived key)           (CRNN + vocab/format rescoring + checkbox CNN + form logic)
 🗂️ lifecycle + event log, retry/back-off          → statuses, calibrated confidences, evidence crops
 💬 WhatsApp-style review (FR/EN)        ◄──      /session/…/finalize   booklet consistency rules
 🔗 patient match (midwife decides)      ◄──►     /match/propose|decide  registry: random ids + code + facts
 ☁️ outbox                               ──►      /records  idempotent central store (encrypted at rest)
                                                   /dashboard anonymised aggregates
```

* **Phone** `work/strat15/app/` — capture, quality gate, encrypted queue, conversational review, manual entry,
  multi-page sessions, re-scan diff, sync. Plain HTML/JS, no framework, served by the box, cached by a service worker.
* **Edge box** `work/strat20/edge_server.py` — the AI runs inside the health facility: real patient data never goes
  to a third-party service, and pages are processed in minutes even when the internet is down for days.
* **Extraction pipeline** `work/strat2/extract_zonal.py` — see below.

## Design choices (and why)

1. **Start from the schema, not from OCR.** The 8 page types are fixed forms. Exact ground truth was built from the
   specimen PDF text layer + vector checkboxes (`work/strat1`); every field has a zone on a template.
2. **Registration, then reading cells.** Paper quad → page type (8 templates; *précoce*/*tardif* twins told apart
   from content) → ECC homography on an illumination-invariant "ink darkness" map (shadows do not break it).
   Median error 1.6 px clean, 3.5 px on phone-like photos.
3. **A small specialised recogniser beats a general model here.** A 6.7 M-parameter CRNN trained on ~400 k synthetic
   field crops (69 handwriting fonts + print, FR/EN/AR, 7 tick styles, phone degradations, pushed through the real
   registration) — 0.84 vs 0.65 for a local 3 B vision-language model on the same crops, 100× faster.
4. **Constrain the answer, not the eye.** Each reading is re-scored by its CTC likelihood against the field's grammar
   and vocabulary (dates, BP, number + unit, enums in FR/EN/AR, official Moroccan regions/provinces); three
   horizontal stretches of the crop vote at string level (fixes "11"→"1"). +10 pts on filled fields.
5. **The booklet checks itself.** DPA = DDR + 280 d, term = DPA + 7 d, gestational ages, newborn age in days, same fact
   on two pages: a rule only changes a value if the recogniser finds the implied value plausible, never a value
   the midwife confirmed, never a blank.
6. **Confidence means something.** Signals → logistic + isotonic calibrator fitted on synthetic pages only
   (ECE ≈ 0.01 on the real test pages). Status thresholds were set so that auto-accepted fields are ≥ 99.5 % correct.
7. **Never hide doubt — at page level too.** A page that cannot be registered (other registry model, wrong page,
   very bad photo) is declared *non reconnue*: no field is ever `CONNU`, the agent asks for a retake or manual entry.

## Status model

| Status | When |
|---|---|
| `CONNU` | read, calibrated confidence ≥ 0.95 (or confirmed by the midwife) |
| `À_RÉVISER` | read but doubtful (0.35–0.95), rule conflict, poor photo, several boxes ticked in an exclusive group |
| `ILLISIBLE` | ink present but unreadable (confidence < 0.35, scribbles) |
| `INCONNU` | the midwife wrote "?", "inconnu", "NSP"… |
| `NON_FOURNI` | empty box, written dash, no box ticked in an exclusive group |
| `NON_APPLICABLE` | empty and excluded by the form's logic (caesarean indication after vaginal delivery, RAI when Rh+, scar when no caesarean…) |

## Privacy

* Identifier zones (name, husband, CIN, phone, address, printed name header) are **masked before any reading** and
  never stored; a leak scanner checks every output (0 leaks in all evaluation runs).
* The **kept "original image"** is the original photo with those zones painted over (computed on the box from the
  registration); the raw photo is discarded after processing. It stays encrypted on the phone.
* Patients are identified by the **random code written on the registry** + non-identifying facts (DDR, due date);
  internal ids are random UUIDs. Candidates tolerate OCR confusions (1/7, 0/O…). The agent never creates a patient
  when a match is plausible: [Patiente 1] [Patiente 2] [Aucune, créer] [Je ne sais pas].
* Encryption at rest: phone (AES-GCM, PBKDF2 200 k from the PIN), box state (AES-GCM, scrypt from `DAYONE_BOX_KEY`).

## Results (80 specimen pages, never used for training; full pipeline)

See [`work/RESULTS_SUMMARY.md`](work/RESULTS_SUMMARY.md) for the definitive table, the per-status confusion matrix
and the honest variants (fonts held out, leave-one-patient-out vocabularies).

## Known limits

* The provided images are clean renders of synthetic pages + 5 real photos of a *different* registry model. We
  degrade the renders ourselves (blur, shadows, skew, low light, occlusion) to test robustness; real photos of the
  real booklet are rejected as *page non reconnue* (correct behaviour, but not read).
* Arabic and English accuracy is measured on synthetic pages only (the specimen has no Arabic).
* Long free-text fields (facility names, comments) are the weakest; they are asked to the midwife.
* WhatsApp: the dialogue runs in a WhatsApp-style web app; a Cloud API adapter exists (`work/strat14`) but was not
  connected to a real sandbox (needs a Meta test number; real data must not go to a third party).
* The box seeds demo patients through `/admin/seed`: disable it on a real deployment; role-based access to the
  masked image is enforced by the device PIN only (single-midwife device).
