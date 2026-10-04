# DayOne · Strategy 8: Offline state machine, encrypted store, sync queue + chaos tests

| | |
|---|---|
| **Status** | DONE (Claude Code, 2026-10-03) |
| **Priority** | P1 |
| **Effort** | 5–6 h |
| **Depends on** | schema from strategy 1 (a stub is fine to start) |
| **Rubric lines** | Offline robustness (15); part of Linking & privacy (10); Code & docs (5) |
| **Work folder** | `dayone-participants/work/strat8/` |

---

## 1. Context you need

Brief, task 4–5 and 8: offline-first (simulated): **encrypted local storage**, a queue "En attente de traitement IA", then upload, processing and sync when connectivity returns. Lifecycle: **CAPTURÉ → EN_ATTENTE_IA → TRAITÉ_IA → À_RÉVISER → VALIDÉ → PATIENTE_LIÉE → ENREGISTRÉ → SYNCHRONISÉ**, plus failure states (processing failure, sync failure, suspected duplicate, manual review required). Keep the original image linked to record ID, capture date, midwife ID and processing status. Rubric: *"Aucun enregistrement perdu ; file d'attente, états et synchronisation corrects quand la connexion tombe et revient."* Tip: *"Modéliser le mode hors ligne comme une machine à états et le tester en coupant la connexion en cours de route."*

## 2. The idea

Implement the lifecycle as an explicit, persisted **state machine** with an **encrypted SQLite store** and an **idempotent outbox**, then prove "no record is ever lost" with **property-based stateful tests** and a **chaos script** that cuts the network and kills the process at every step.

## 3. Why it could score

A test suite that injects failures and checks invariants is far stronger evidence than a toggle switch in a demo, and it is plain software engineering (low risk, high reliability).

## 4. Implementation plan

### 4.1 Setup and files

```bash
pip install cryptography hypothesis fastapi uvicorn httpx pytest
# optional: sqlcipher3-wheels for full-database encryption
```

```
work/strat8/
  lifecycle.py        # states, transitions, guards
  store.py            # encrypted SQLite (records, fields, images, events, outbox)
  crypto.py           # key derivation + AES-GCM helpers
  outbox.py           # sync worker with back-off and idempotency keys
  mock_server.py      # FastAPI: /records (idempotent upsert), /process (fake AI)
  netsim.py           # connectivity flag + fault injector
  tests/test_stateful.py  tests/test_crypto.py  tests/test_outbox.py
  chaos.py
  LIFECYCLE.md        # state diagram (Mermaid) for the project README
```

### 4.2 States and transitions

```python
TRANSITIONS = {
  "CAPTURÉ":        {"EN_ATTENTE_IA"},
  "EN_ATTENTE_IA":  {"TRAITÉ_IA", "ÉCHEC_TRAITEMENT"},
  "ÉCHEC_TRAITEMENT": {"EN_ATTENTE_IA", "RÉVISION_MANUELLE_REQUISE"},   # retry or manual entry
  "TRAITÉ_IA":      {"À_RÉVISER", "VALIDÉ"},
  "À_RÉVISER":      {"VALIDÉ", "CAPTURÉ"},                               # retake photo → new capture
  "RÉVISION_MANUELLE_REQUISE": {"VALIDÉ"},
  "VALIDÉ":         {"PATIENTE_LIÉE", "DOUBLON_SUSPECTÉ"},
  "DOUBLON_SUSPECTÉ": {"PATIENTE_LIÉE"},
  "PATIENTE_LIÉE":  {"ENREGISTRÉ"},
  "ENREGISTRÉ":     {"SYNCHRONISÉ", "ÉCHEC_SYNCHRO"},
  "ÉCHEC_SYNCHRO":  {"ENREGISTRÉ"},                                      # re-queued
  "SYNCHRONISÉ":    set(),
}
GUARDS = {
  ("TRAITÉ_IA", "VALIDÉ"): lambda r: not any(f.status == "À_RÉVISER" for f in r.fields),
  ("VALIDÉ", "PATIENTE_LIÉE"): lambda r: r.match_decision is not None,   # midwife decided
}
```

Every transition = one SQLite transaction that updates `records.state` and appends to `events(record_id, from, to, at, actor, reason)`.

### 4.3 Encryption

- Key: derived from the device PIN with scrypt (`cryptography.hazmat.primitives.kdf.scrypt`) + random salt stored locally; key kept in memory only.
- Field values and images: AES-GCM per blob (`AESGCM(key).encrypt(nonce, data, aad=record_id)`), nonce 12 random bytes stored with the blob. Images on disk as `*.bin`, never as `.jpg`.
- Alternative: SQLCipher for the whole DB file; compare effort.

### 4.4 Outbox and sync

- Items: `(idempotency_key = record_id + ":" + version, payload, attempts, next_try_at)`.
- Worker: when `netsim.online`, send oldest first; on 2xx mark SYNCHRONISÉ; on error exponential back-off (cap 10 min) and ÉCHEC_SYNCHRO after N attempts (re-queued on next connectivity change).
- Server dedupes by idempotency key (returns 200 for duplicates).
- Re-digitised registry (brief task 7): server version vs local edit → conflict record for strategy 9 to resolve with the midwife.

### 4.5 Crash recovery

On start-up: records stuck in transient states (EN_ATTENTE_IA while processing, outbox items "in flight") are re-queued. Processing is idempotent (same image → same result id).

## 5. How to test it

### 5.1 Property-based stateful test (`hypothesis.stateful.RuleBasedStateMachine`)

Rules: capture, process, review (confirm / edit / retake), link, register, sync, network up / down, server error, duplicate delivery, crash + restart. Invariants after every step:

1. No record disappears (count of captured records only grows).
2. Every record is in exactly one legal state; every state change is in `TRANSITIONS`.
3. Every SYNCHRONISÉ record exists on the server exactly once, with the same content hash.
4. The event log replayed from scratch reproduces the current states.

Run ≥ 10,000 steps (`settings(max_examples=200, stateful_step_count=50)`).

### 5.2 Chaos script

`python chaos.py --records 500 --kill-prob 0.05 --drop-prob 0.3` → kills the worker process at random points, flips connectivity, injects 500s and duplicate acks. Final reconciliation: 0 lost, 0 duplicated, all records eventually SYNCHRONISÉ or in an explained failure state.

### 5.3 Encryption checks

Open the DB file with plain `sqlite3`: values unreadable; grep the raw DB and image files for known field values → 0 hits; wrong PIN → decryption fails cleanly.

### 5.4 Demo scenario (required by the brief)

Scripted: offline capture → connectivity returns → AI processing → review of an uncertain field → match decision → synced. Must pass 3 runs in a row.

### 5.5 Acceptance

All invariants hold over ≥ 10,000 steps; chaos run clean; encryption checks pass; demo passes 3 times.

## 6. Risks

Building a sync protocol that is too clever. A single-writer device + idempotent upsert is enough for the prototype; document the multi-device limitation.

## 7. Combines with

Strategy 9 (UI triggers transitions), 10 (linking state, role-based image access), 2 / 3 (processing step), 4 (quality gate at capture).

## 8. Results log

| Date | Who | Hypothesis steps | Chaos result | Encryption checks | Demo runs | Notes |
|---|---|---|---|---|---|---|
| 2026-10-03 | Claude Code | 150 examples x 60 steps (~9,000) with network flaps, 500s, duplicate acks, crash/restart | 50 records, 7 injected server errors: all SYNCHRONISÉ, 0 lost, 0 duplicated | DB + WAL grep: 0 plaintext values / image bytes; wrong PIN rejected | n/a (PWA demo in strategy 15) | `pytest work/strat8` 3/3 |

**Implementation notes (2026-10-03).** SQLite store, AES-GCM per blob with scrypt-derived key, event log replay reproduces states, idempotent outbox keyed by record:version, role-restricted and logged access to the original photo.
