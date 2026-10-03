# OptiFrame · Strategy 19: Server-side processing path with hybrid routing (fallback for weak phones and heavy models)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (risk reduction for the 15 app points and the 30-second limit) |
| **Effort** | 3–4 h |
| **Depends on** | the Python reference pipeline (strategies 2, 3, 5 / 6, 8, 9) |
| **Rubric lines** | Mobile web app (15: works on the jury's phone), Robustness (10: no crash), performance limit (< 30 s per pair), Data & AI (15: heavier models usable) |
| **Differs from 1–10** | Strategy 10 runs everything **in the browser**. This adds a **Python server** with the same API, and routes each request in-browser or server-side depending on device capability, model availability and connectivity |
| **Work folder** | `optiframe-participants/work/strat19/` |

---

## 1. Context you need

- The brief recommends in-browser processing but allows a Python server *"si son URL reste active jusqu'à la fin des délibérations"*; free hosting suggestions include Hugging Face Spaces and Render; tunnels are tolerated during evaluation. No paid services or closed APIs in the final version.
- The jury uses **their own phone**, possibly old or with an unusual browser; WebAssembly OpenCV and ONNX models may be slow or fail there.

## 2. The idea

1. A FastAPI service exposing `/measure` (image(s) + eye + options → contour, A, B, perimeter, control images) and `/frame` (two contours + bridge → STL), running the Python reference pipeline (OpenCV + PyTorch / ONNX models).
2. The web app decides per request:
   - **in-browser** if the device passes a quick capability test (WASM loaded, a 1-second benchmark under a threshold) and the model is available locally;
   - **server** otherwise, or automatically after an in-browser failure / timeout;
   - a user-visible toggle for the demo.
3. **Parity guarantee:** both paths produce the same numbers on the same image (shared test images, tolerance 0.05 mm).

## 3. Why it could score

It removes the single point of failure "the jury's phone can't run our WASM", keeps the 30-second limit on weak phones, and lets us use a heavier, more accurate segmentation model server-side if it helps.

## 4. Implementation plan

### 4.1 Files

```
work/strat19/
  server/app.py          # FastAPI, /measure, /frame, /health
  server/pipeline.py     # imports the Python reference implementation
  server/Dockerfile      # for Hugging Face Spaces (Docker) or Render
  client/router.js       # capability test, routing, timeout fallback
  parity_tests/          # images + expected outputs; test runner for both paths
  ops.md                 # hosting, keep-alive, logs, deadline (must stay up until deliberations end)
```

### 4.2 Operational details

- Free tiers may **sleep when idle** (cold starts of 30–60 s): schedule a keep-alive ping during the evaluation window, or warm the server right before the demo; measure cold-start time.
- Limit image size client-side (downscale to what the pipeline needs) to keep uploads fast on 4G.
- Privacy: images are processed in memory and not stored (state it in the UI and README); no personal data involved (lenses only).
- CORS restricted to the app's origin; request size limits; simple rate limit.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Parity | in-browser vs server results on 20 test images: A/B within 0.05 mm |
| T2 | Routing | on a deliberately weak device (or with WASM disabled), the app silently uses the server and completes |
| T3 | Timing | server path ≤ 30 s per pair on 4G including upload; cold start measured and mitigated |
| T4 | Failure handling | server down → clear message and in-browser attempt; both down → helpful message, no crash |
| T5 | Uptime | URL monitored during the event window (simple cron ping log) |

## 6. Risks

Hosting limits (memory for PyTorch models on free tiers); prefer ONNX Runtime on the server too, and test memory usage.

## 7. Combines with

Strategy 10 (app), 5 / 6 (heavier models server-side), 9 (frame generation either side), 18 (same results regardless of path).

## 8. Results log

| Date | Who | Host | Parity max diff | Pair time (server) | Cold start | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
