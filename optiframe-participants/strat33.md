# OptiFrame · Strategy 33: Fiducial-board pose uncertainty cross-check

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Depends on** | strategy 1 ChArUco board; strategy 2 homography |
| **Work folder** | `optiframe-participants/work/strat33/` |

## 1. Context and evidence

The current pipeline interpolates ChArUco corners and rectifies synthetic images. Its report explicitly warns that reprojection residual does not prove real accuracy. OpenCV's official ChArUco guide documents corner interpolation and pose estimation through `matchImagePoints` and `solvePnP`; this supports a second pose diagnostic, but does not validate the physical rig. Strategy 2 already uses the homography; this proposal checks board-plane model disagreement and is explicitly blind to lens-edge height/parallax.

Evidence: [metrology report](work/strat2/report.md) warns reprojection residual is not physical accuracy; see [official OpenCV ChArUco pose guide](https://docs.opencv.org/5.0/tutorials/objdetect/charuco_detection/charuco_detection.html).

## 2. Idea and distinction

Estimate board pose and camera intrinsics where available, project known board points back into the image, and compare this pose-based mapping with the planar homography. Report local metric disagreement across the board plane and reject frames with unstable pose. It cannot diagnose raised lens edges because both estimates use board markers on the same plane; strategy 13 addresses that different observable.

## 3. Rubric relevance

Adds a measurable geometric consistency check and may identify captures where one global plane mapping is unreliable.

## 4. Implementation steps

Add `work/strat33/pose_check.py`, a versioned board spec, and diagnostic overlays. Record camera-model assumptions and compare local pixel-to-mm scale grids. Keep strategy 2 outputs as reference.

## 5. Proposed experiment

Run 15 synthetic board views with controlled camera tilt and intrinsics plus 10 board-only controls; do not vary or infer lens-edge height. Baseline: homography alone. Adopt a warning if pose and homography predict board-plane coordinates within 0.2 mm on held-out markers and clean controls trigger under 10% false warnings; kill if the second estimate adds no useful failure detection. Proposed thresholds, not measured.

## 6. Risks

Intrinsics from metadata may be inaccurate; this diagnostic cannot detect same-plane parallax or raised lens-edge bias. Synthetic camera assumptions cannot establish physical pose accuracy.

## 7. Combinations

Pairs with strategies 1, 2, 13, 21, and 25.

## 8. Results log

NOT RUN. ChArUco pose cross-check is proposed; physical rig remains unvalidated.
