# OptiFrame · Strategy 22: Display refresh and rolling-shutter banding check

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 screen lightbox; strategy 10 capture app |
| **Work folder** | `optiframe-participants/work/strat22/` |

## 1. Context and evidence

Strategy 1 uses a laptop/tablet screen as a backlight and the phone camera is handheld; no real-phone capture is reported. Some display illumination and camera rolling-shutter combinations can create horizontal bands or temporal brightness changes. Existing strategy 24 checks clipping and contrast, not periodic banding or capture/display timing. This tests that interaction specifically and does not recheck printed dimensions.

Evidence: [CONTINUATION.md](../CONTINUATION.md) records the planned screen-light rig; no phone captures are reported.

## 2. Idea and distinction

Capture uniform lightbox frames at several exposure conditions and brightness settings, then measure row-wise luminance periodicity and frame-to-frame stability. If bands appear, guide the user to a stable screen brightness or exposure lock and acquire a new capture. Keep the lens boundary pipeline unchanged; do not confuse illumination artifacts with lens edges.

## 3. Rubric relevance

Protects measurement units and 1:1 contour/frame export from a basic but consequential scale error.

## 4. Implementation steps

Add `work/strat22/banding.py`, a uniform screen target, and a local report. Record screen model, refresh/brightness setting, phone, camera mode, and exposure metadata when available. Keep raw captures local; use synthetic sinusoidal row patterns to test detector sensitivity and specificity.

## 5. Proposed experiment

On two phones, capture 30 blank-screen frames at three brightness levels and two display refresh settings if available, plus 20 synthetic banded controls; baseline is uncontrolled auto-exposure. Adopt a warning only if it detects at least 90% of synthetic banding with under 5% false positives on stable frames and identifies a repeatable real-device setting issue. If no real bands occur, record that and do not add a warning. Proposed thresholds, not measured.

## 6. Risks

Screen PWM may not be exposed in metadata; banding can vary with camera mode and exposure. A small device sample cannot certify broad compatibility.

## 7. Combinations

Complements strategies 1, 10, 24, and 32.

## 8. Results log

NOT RUN. No screen/camera banding measurements are reported.
