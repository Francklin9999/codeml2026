# DayOne — a midwife, a phone and an AI

An offline-first, WhatsApp-style agent that turns photos of the paper maternal registry into a structured,
verified, longitudinal record. The midwife keeps her paper registry; the phone reads it, **shows only what it is
unsure about**, keeps everything encrypted until the network returns, and links each visit to the right woman by
the code written on the registry — never by her name.

| | |
|---|---|
| Demo script | [`DEMO.md`](DEMO.md) (offline capture → connectivity back → review of an uncertain field → match decision) |
| Record lifecycle | [`LIFECYCLE.md`](LIFECYCLE.md) (one transition table shared by the app and the tested model) |
| Measured results | [`work/RESULTS_SUMMARY.md`](work/RESULTS_SUMMARY.md), every run in [`work/results.md`](work/results.md) |
| What would need an external resource | [`AMELIORATIONS_EXTERNES.md`](AMELIORATIONS_EXTERNES.md) (Gemini, data collection day, bigger GPU, WhatsApp) |

> The organizers' dataset (`data/`: specimen PDF, page images, synthetic CSV) is not in the repository. Put it back in `data/` before running.

## Quick start (≈ 5 min, no training needed)

```bash
pip install -r requirements.txt          # GPU optional: install torch from the CUDA index first for speed
./run_box.sh                             # Windows: .\run_box.ps1  → app on http://localhost:8765 (box's own browser)
./run_box.sh 8765 --https                # Windows: .\run_box.ps1 -Https → phones on the Wi-Fi: https://<box-ip>:8765
pytest work                              # 46 tests: lifecycle/chaos, crypto, dialogue, linking, rules, box API
```

On a phone: open `https://<box-ip>:8765`, choose a PIN (and the midwife id), and type the **6-digit pairing code
printed by the box** when the agent asks for it: the phone receives its own random device token, bound to that
midwife. The phone's encryption (WebCrypto) requires HTTPS. The box's self-signed certificate (accepted once) is
enough while the box is reachable; to reopen the app offline, away from the box, install a locally trusted
certificate with mkcert (see `work/strat20/make_cert.py`). The box's own browser can use `http://localhost:8765`.
A full automated rehearsal runs at `http://localhost:8765/?db=e2e&e2e=1`.

Trained models ship in `models/` (CRNN 13 MB fp16, checkbox CNN 0.3 MB, calibrator as plain JSON). Page templates
are rebuilt from the specimen PDF automatically on first use. Re-training everything is documented in
`work/` (synthetic data generation + a few hours on a laptop GPU).

## Architecture

```
 phone (PWA, works offline)                       facility edge box (local Wi-Fi, no internet needed)
 ─────────────────────────────                    ───────────────────────────────────────────────────
 📷 capture + on-device quality gate     ──►      /process   register page (any orientation) → mask identifiers →
 🔐 IndexedDB, AES-GCM (PIN-derived key)           read every field (CRNN + grammar-constrained rescoring +
 🗂️ lifecycle + event log, retry/back-off          checkbox CNN + form logic) → statuses, calibrated confidences,
 💬 WhatsApp-style review (FR/EN)        ◄──       evidence crops
 🔗 patient match (midwife decides)      ◄──►     /session/…/finalize  booklet consistency rules
 ☁️ outbox                               ──►      /match/propose|decide  registry: random ids + code + facts
                                                   /records  idempotent central store (encrypted at rest)
                                                   /dashboard anonymised aggregates
                                                   every API call: paired phone (token) or the box itself
```

* **Phone** `work/strat15/app/` — capture, quality gate, encrypted queue, conversational review, manual entry,
  multi-page sessions, re-scan diff, sync, resume after a restart. Plain HTML/JS, no framework, served by the box;
  the service worker caches only the app shell (never an API response).
* **Edge box** `work/strat20/edge_server.py` — the AI runs inside the health facility: real patient data never goes
  to a third-party service, and pages are processed in minutes even when the internet is down for days.
* **Extraction pipeline** `work/strat2/extract_zonal.py` — see below.

## Design choices (and why)

1. **Start from the schema, not from OCR.** The 8 page types are fixed forms. Exact ground truth was built from the
   specimen PDF text layer + vector checkboxes (`work/strat1`); every field has a zone on a template.
2. **Registration, then reading cells.** Paper quad → page type (8 templates; *précoce*/*tardif* twins told apart
   from content) → ECC homography on an illumination-invariant "ink darkness" map (shadows do not break it);
   sideways or upside-down photos are turned back. Median error 1.6 px clean, 3.5 px on phone-like photos — and a
   test with the *true* homography showed that registration is not what limits accuracy on degraded photos.
3. **A small specialised recogniser beats a general model here.** A 6.7 M-parameter CRNN trained on ~600 k
   synthetic field crops (69 handwriting fonts + print, FR/EN/AR, 7 tick styles; an irregular "writer" — slant,
   spacing, baseline wander, pen width, elastic distortion — so that it does not learn a font's exact geometry;
   phone degradations; pushed through the real registration). 0.84 vs 0.65 for a local 3 B vision-language model
   on the same crops, 100× faster.
4. **Constrain the answer, not the eye.** Each reading is re-scored by its CTC likelihood against the field's grammar
   and vocabulary (dates, BP, number + unit, enums in FR/EN/AR, official Moroccan regions/provinces). When the free
   reading is not a valid value (a blurred "152" read "1"), a grammar-constrained CTC beam search proposes the most
   likely valid ones. Three horizontal stretches of the crop vote at string level (fixes "11"→"1").
5. **The booklet checks itself.** DPA = DDR + 280 d, term = DPA + 7 d, gestational ages, newborn age in days, same
   fact on two pages, and in the visit table: next appointment = visit + 28 d, fundal height = SA − 4
   (McDonald). A rule only changes a value if the recogniser finds the
   implied value plausible, never a value the midwife confirmed, never a blank — and every change is shown to her
   with both readings.
6. **Confidence means something.** Ten reading signals → logistic calibrator fitted on synthetic pages only, stored
   as plain JSON (no pickled model). A value is auto-accepted (`CONNU`) only if calibrated confidence ≥ 0.95 **and**
   it respects its field's format and plausible range; a blank read with confidence < 0.9 is asked, not declared
   empty. We report the strict metrics: share auto-accepted, error rate among `CONNU`, written values silently
   declared blank, questions per page.
7. **Never hide doubt — at page level too.** A page that cannot be registered (other registry model, wrong page,
   very bad photo) is declared *non reconnue*: no field is `CONNU`, no image crop leaves the box, the photo is
   deleted from the phone, and the agent asks for a retake or manual entry.

## Status model

| Status | When |
|---|---|
| `CONNU` | read, calibrated confidence ≥ 0.95 and valid format/range (or confirmed by the midwife); checkboxes: checkbox CNN ≥ 80 % sure (its probabilities are calibrated, ECE ≈ 0.003) |
| `À_RÉVISER` | read but doubtful (0.35–0.95), invalid format/range, changed or flagged by a booklet rule, poor photo, several boxes ticked in an exclusive group, blank read with low confidence |
| `ILLISIBLE` | ink present but unreadable (confidence < 0.35, scribbles) |
| `INCONNU` | the midwife wrote "?", "inconnu", "NSP"… |
| `NON_FOURNI` | empty box, written dash, no box ticked in an exclusive group |
| `NON_APPLICABLE` | empty and excluded by the form's logic (caesarean indication after vaginal delivery, RAI when Rh+, scar when no caesarean…) |

## Privacy and security

* Identifier zones (name, husband, CIN, phone, address) are **masked before any reading** and never stored; the
  masks are widened when the registration is weak. The printed name header of the post-partum pages is not a field
  (never read) and is painted over in the kept image. Every output passes a scanner for identifier patterns (CIN,
  phone, address); it is a safety net, not the protection.
* The **kept "original image"** is the original photo with those zones painted over (computed on the box from the
  registration); the raw photo is discarded after processing — and deleted outright when the page could not be
  registered (the zones could not be located). It stays encrypted on the phone and is synced with the record
  (capture time, midwife id, image hash). **Access by role** (`GET /records/{id}/image`): a midwife's paired phone sees
  the images of the records she captured (her id is bound to the device token at pairing, not declared per
  request), a device paired with the supervisor code sees all, and every access is logged (encrypted).
* Patients are identified by the **random code written on the registry** + non-identifying facts (DDR, due date);
  internal ids are random UUIDs. The code is confirmed by the midwife unless read with certainty. Candidates
  tolerate OCR confusions (1/7, 0/O…). The agent never creates a patient when a match is plausible:
  [Patiente 1] [Patiente 2] [Aucune, créer] [Je ne sais pas].
* Encryption at rest: phone (AES-GCM, PBKDF2 200 k from the PIN; the browser cache holds only the app shell), box
  state (AES-GCM, scrypt from `DAYONE_BOX_KEY`, or a random key generated once into the state folder — no default
  key). Only paired devices (random 192-bit token obtained once with a 6-digit start-up code; only its hash is
  stored; failed attempts rate-limited) or the box itself can call the API; demo seeding only from the box; HTTPS
  between phone and box.

## Results (80 specimen pages, never used for training; full pipeline)

See [`work/RESULTS_SUMMARY.md`](work/RESULTS_SUMMARY.md) for the definitive tables (all photo qualities, accuracy on
the photos the quality gate accepts, strict uncertainty metrics) and the honest variants (handwriting fonts held
out, leave-one-patient-out vocabularies).

## Known limits (and evaluation biases we declare)

* The provided images are clean renders of synthetic pages + 5 real photos of a *different* registry model. We
  degrade the renders ourselves (blur, shadows, skew, low light, occlusion) to test robustness; real photos of the
  real booklet are rejected as *page non reconnue* (correct behaviour, but not read). `AMELIORATIONS_EXTERNES.md` §3
  describes the one-day data collection that would close this gap without any patient data.
* Tuned on the test set — declared: the visit-table rules (appointment + 28 d, fundal height = SA − 4) were found
  by inspecting the specimen ground truth (they are also standard care practice and only repair under the
  likelihood test); the blur threshold of the quality gate and the page-verdict thresholds were chosen on runs over
  the specimen pages; the field grammars, enum vocabularies and plausible ranges are inferred from the specimen
  ground truth (leave-one-patient-out during evaluation, all 10 patients once deployed). The recogniser and the
  calibrator never saw a specimen page.
* The shipped recogniser was trained with the specimen's handwriting fonts (public Google fonts) among 69. Trained
  without them, the same recipe reads 0.939 of the filled fields on clean pages and 0.718 on phone-like photos
  (`RESULTS_SUMMARY.md`): that is the figure to expect on new handwriting.
* Arabic and English accuracy is measured on synthetic pages only (the specimen has no Arabic).
* *Précoce* / *tardif* mother pages are told apart on the box from the delivery date read on page 4 of the same
  session: photograph page 4 before pages 5–8 (the evaluation reads the booklet in that order).
* Long free-text fields (facility names, comments) are the weakest; they are asked to the midwife.
* Manual entry (AI unavailable / page not recognised) covers the main inline fields of each page, not the
  280-cell visit table: those are completed from a retaken photo.
* The form has no hepatitis C field (only Ag HBs), so it is not extracted.
* One midwife per device: the PIN protects the phone and the midwife id is declared on it; roles on the box are
  sage-femme (paired phone) and superviseure (supervisor code). WhatsApp: the dialogue runs in a WhatsApp-style
  web app; a Cloud API adapter exists (`work/strat14`) but needs a Meta test number, and real data must not go
  through a third party. The box seeds demo patients through `/admin/seed`: disable it on a real deployment.
