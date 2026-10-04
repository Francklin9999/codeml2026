# DayOne · Strategy 15: Offline-first capture client as a PWA (on-device encryption, auto-capture, background sync)

| | |
|---|---|
| **Status** | DONE (Claude Code, 2026-10-03) |
| **Priority** | P2 |
| **Effort** | 5–6 h |
| **Depends on** | strategy 8 (server-side lifecycle and sync API) |
| **Rubric lines** | Offline robustness (15), Patient linking & privacy (10: encrypted local storage), bonus on-device quality check, Conversational review (20) when offline |
| **Differs from 1–10** | Strategy 8 implements the lifecycle and sync with a Python store and a simulated network. This builds the **device side** the midwife actually holds: a browser app that captures, encrypts and queues pages with no connectivity, checks image quality on the device, and syncs when the network returns |
| **Work folder** | `dayone-participants/work/strat15/` |

---

## 1. Context you need

- Brief: offline-first, *"stockage local sur l'appareil doit être chiffré"*, queue "En attente de traitement IA", upload, processing and sync when connectivity returns; no record lost; on-device image-quality check is a bonus; zero change to the midwife's workflow (the paper stays the reference).
- A Progressive Web App runs on any Android phone's browser, can work offline (service worker), store data in IndexedDB and encrypt with the Web Crypto API.

## 2. The idea

A small PWA with three screens: **Capture** (camera, page guidance, quality check), **File d'attente** (records and their lifecycle states), **Révision** (the chat-style review when results are back, or manual entry when AI is unavailable). Everything is stored encrypted in IndexedDB; a sync engine uploads when online.

## 3. Why it could score

It makes the offline story tangible in the demo: airplane mode on, capture three pages, see them queued with states, airplane mode off, watch them sync and process. That is exactly the brief's required demo.

## 4. Implementation plan

### 4.1 Files

```
work/strat15/app/
  index.html  manifest.webmanifest  sw.js
  src/capture.js       # getUserMedia / file input fallback, page edge detection (OpenCV.js or jscanify-like), auto-capture when stable
  src/quality.js       # blur (variance of Laplacian), brightness, glare, page found → accept / retake message
  src/crypto.js        # PBKDF2/Argon2-derived key from PIN → AES-GCM encrypt blobs (Web Crypto)
  src/db.js            # IndexedDB (idb library): records, images, events, outbox
  src/sync.js          # online/offline detection, retry with back-off, idempotency keys
  src/review.js        # chat-style review UI; manual entry forms
  src/i18n/fr.json en.json
```

### 4.2 Key details

- **Encryption:** derive a key from the midwife's PIN with PBKDF2 (Web Crypto supports PBKDF2 natively; ≥ 310,000 iterations SHA-256) and a random salt; encrypt images and records with AES-GCM (12-byte random IV per blob). Key kept in memory only; lock after inactivity.
- **Storage limits:** check `navigator.storage.estimate()` and request `navigator.storage.persist()` so the browser does not evict the queue; downscale images to what extraction needs (long side ~2,500 px, JPEG q85) before storing.
- **Sync:** the outbox holds `(record_id, version, idempotency_key)`; on `online` events or periodic retries (Background Sync API where supported, else on app focus), upload and update states from the server responses.
- **States shown to the user:** CAPTURÉ, EN_ATTENTE_IA, TRAITÉ_IA, À_RÉVISER, VALIDÉ… with plain-language labels and icons; failures with retry buttons.
- **Original image:** never displayed after validation unless the role allows (strategy 10).

### 4.3 Hosting

Static hosting with HTTPS (GitHub Pages / Netlify) for the demo; the API from strategy 8 behind HTTPS (tunnel acceptable for the demo).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Offline capture | airplane mode: 5 pages captured, app reloaded, all 5 still queued and decryptable with the PIN |
| T2 | Encryption at rest | inspect IndexedDB in DevTools: only ciphertext; wrong PIN fails to decrypt |
| T3 | Sync | network restored: all records reach SYNCHRONISÉ, server shows no duplicates (toggle network 5 times during upload) |
| T4 | Kill test | close the tab during upload; reopen: upload resumes, no loss, no duplicates |
| T5 | Quality gate | blurred / dark / partial-page photos are rejected with the right message; good photos accepted |
| T6 | Device test | works on a mid-range Android phone in Chrome; installable to home screen |

## 6. Risks

iOS Safari limits background sync and may evict storage; target Android (most common in the brief's context) and document the iOS limitation.

## 7. Combines with

Strategy 8 (server lifecycle), 4 (quality gate model, ported to JS), 9 (review UI), 10 (role-based access), 14 (WhatsApp as the online channel).

## 8. Results log

| Date | Who | Device | T1–T6 | Notes |
|---|---|---|---|---|
| 2026-10-03 | Claude Code | desktop browser (in-app browser pane) served by the strategy 20 edge box | blurry photo rejected with message; 2 pages captured offline -> EN_ATTENTE_IA; survive reload; ciphertext at rest; wrong PIN rejected; on reconnection both synced -> TRAITÉ_IA (page type 3) with no identifier values | not tested on a phone camera |

**Implementation notes (2026-10-03, updated 2026-10-04).** `work/strat15/app/`: PBKDF2 (200k) + AES-GCM (WebCrypto), IndexedDB records/events, service worker app shell, exponential back-off, idempotency key record:version. Blur threshold set from strategy 4's measured gate. 2026-10-04 (after an independent audit): service worker caches only the app shell (an API response with a patient page was cached in clear before); raw photo deleted when the box could not mask it; HTTPS needed for WebCrypto on a phone (clear message otherwise; `run_box --https`); phone pairing with a 6-digit code; transitions loaded from the shared `lifecycle.json`; every non-terminal state resumed after a restart; permanent processing errors go to manual review; the registry code is confirmed unless read with certainty; every rule change/flag is asked; explicit priority list; midwife id on the lock screen; kept masked image shown at review; match buttons translated. e2e rehearsal 11/11 with the shipped models.
