# DayOne · Strategy 20: On-site edge AI box for the health centre (offline processing on the local network)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (architecture differentiator; prototype-level) |
| **Effort** | 4–5 h |
| **Depends on** | an extractor that runs locally (strategy 2 / 11, or a small quantised VLM from strategy 3), strategy 8 (lifecycle API) |
| **Rubric lines** | Offline robustness (15), Patient linking & privacy (10: data never leaves the facility), Extraction (30: processing available without internet) |
| **Differs from 1–10** | Strategy 8 assumes AI processing happens when internet returns. This adds a **local processing tier**: a cheap box (mini-PC or laptop) in the health centre that runs extraction on the local Wi-Fi with no internet, so pages are processed within minutes even when the internet is down for days |
| **Work folder** | `dayone-participants/work/strat20/` |

---

## 1. Context you need

- Brief: offline-first; queue "En attente de traitement IA", processing and sync when connectivity returns; no real patient data to third parties. In low-resource settings, internet may be absent for long periods, which delays processing and therefore verification while the woman is still present.
- Local models available to us: small recognisers (strategy 11), OpenCV pipelines (strategy 2), quantised VLMs (e.g. Qwen2.5-VL-3B in 4-bit) if the box has a GPU or enough RAM.

## 2. The idea

Three-tier architecture:
1. **Phone** (strategy 15): capture, encryption, queue, review.
2. **Edge box** in the facility (local Wi-Fi hotspot, no internet required): runs extraction, validation and linking against the facility's local registry copy; returns results to phones in minutes.
3. **Central server** (when internet exists): sync, backups, aggregates (strategy 19).

The phone tries the edge box first, then the central server, and otherwise keeps the record in EN_ATTENTE_IA. The same lifecycle and idempotency keys apply across tiers.

## 3. Why it could score

It solves the real-world weakness of "AI when online" (verification would happen days later), keeps data inside the facility (privacy), and is a strong design argument in the README and presentation even as a prototype.

## 4. Implementation plan

### 4.1 Files

```
work/strat20/
  edge_server.py       # FastAPI: /process, /records (same API as strategy 8's server)
  discovery.py         # phone finds the box (mDNS / fixed local IP / QR pairing)
  models/              # quantised models (ONNX / int8 / GGUF), not committed (download script)
  benchmark.py         # latency per page on target hardware
  DEPLOY.md            # hardware list, power, setup, security (local TLS, device pairing)
```

### 4.2 Details

- **Model choices for CPU:** OpenCV registration + small recogniser (strategy 11) as the default path (≈ seconds per page); quantised VLM only for free-text or ambiguous fields if hardware allows.
- **Security:** pair phones with the box via a QR code containing a pre-shared key; TLS with a self-signed certificate pinned in the app; the box stores data encrypted at rest; no internet exposure.
- **Sync:** the box forwards validated records to the central server when internet appears (store-and-forward), using the same outbox logic.
- **Power and cost:** document an example bill of materials (mini-PC or refurbished laptop, battery / UPS) without claiming exact prices unless sourced.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | No-internet processing | laptop as box, internet disabled, phone on local Wi-Fi: page processed and returned for review |
| T2 | Latency | median time per page on CPU-only hardware ≤ 60 s with the default path |
| T3 | Fallback chain | box off → record stays EN_ATTENTE_IA; box on → processed; internet on → synced; no duplicates |
| T4 | Pairing | an unpaired device cannot submit or read records |
| T5 | Accuracy parity | edge results equal the reference pipeline's results on the same pages |

## 6. Risks

Hardware availability and maintenance in the field; present it as an option with a clear fallback (phone queue only).

## 7. Combines with

Strategy 8 (API and lifecycle), 15 (phone client), 11 (small model), 10 (privacy), 19 (central aggregates).

## 8. Results log

| Date | Who | Hardware | Median latency | T1–T5 | Notes |
|---|---|---|---|---|---|
| | | | | | |
