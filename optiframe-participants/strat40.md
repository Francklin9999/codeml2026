# OptiFrame · Strategy 40: Calibration-free camera-mode change sentinel

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 10 camera integration; strategy 2 board detection |
| **Work folder** | `optiframe-participants/work/strat40/` |

## 1. Context and evidence

The physical rig, app, and phone behavior remain untested. Strategy 2 allows phone lens distortion checks; strategy 10 plans a device matrix. Mobile camera APIs can change resolution or switch lenses while focus/zoom changes. This proposal detects an in-session camera-mode switch using observed board geometry, not a calibrated distortion correction or a device-specific calibration database.

Evidence: [CONTINUATION.md](../CONTINUATION.md) records the browser app and physical phone tests as unfinished.

## 2. Idea and distinction

Track stable board features across preview frames and compare field of view, principal-point shift, sharpness, and local homography scale. If a camera switch or digital zoom jump occurs after a measurement preview was accepted, invalidate the capture and reacquire rather than reuse stale calibration. Keep the sentinel advisory until physical behavior is tested.

## 3. Rubric relevance

Prevents a silent camera pipeline change from invalidating measurements during a mobile demo.

## 4. Implementation steps

Add `work/strat40/mode_sentinel.js` and synthetic sequence fixtures. Record camera track settings, dimensions, board corner count, and scale estimates. Trigger a clear recapture state if a discontinuity exceeds a tested limit.

## 5. Proposed experiment

On two phones where available, record 20 stable sequences and 10 deliberate zoom/focus/resolution changes; baseline is no mode-change detection. Adopt if ≥90% of deliberate changes are flagged within two frames, with <5% false alarms on stable sequences. If browsers expose no switch, rely on image geometry and report that limitation. Proposed thresholds, not measured.

## 6. Risks

Focus breathing and hand movement can mimic a mode switch. The detector must not present inferred camera state as guaranteed hardware metadata.

## 7. Combinations

Complements strategies 2, 7, 10, 21, 32, and 33.

## 8. Results log

NOT RUN. No mobile capture sequence or camera-switch test is reported.
