# Error budget: what is measured and what remains unknown

| Contribution | Current evidence | Interpretation |
|---|---|---|
| Board print scale | Nominal 12 mm squares in an exact-size PDF; no physical print measured | Unknown real systematic error; verify the 72 mm span and use a separate measured spec |
| Homography fit | Per-photo RMS residual in `measurement.json`; gate at 0.1 mm | Fit consistency only; does not bound error at the lens or detect all systematic distortion |
| Rim localisation and rasterisation | Synthetic combined A/B MAE 0.080234 mm; maximum 0.312796 mm | Includes the ideal rim rendering, interpolation, segmentation and smoothing; cannot separate these contributions yet |
| Height | Synthetic 3 mm case A/B errors 0.440025/0.369844 mm before correction, 0.020475/0.063320 mm after | Demonstrates the fronto-parallel correction with known inputs; real effective edge height remains unknown |
| Camera distortion | Not modelled or calibrated | Requires physical multi-phone measurements |
| Real optical rim and glare | Ideal synthetic dark band only | Real refraction and bevel edge may differ systematically |
| Horizontal axis | Assumed aligned with the board | Rotation of the lens changes A/B; canonical anatomical orientation remains unfinished |
| Calliper repeatability | NOT RUN | Need three independent readings for each real lens |

Do not combine these values in quadrature yet: most contributions have not been independently measured, and several are systematic or correlated. Complete strategy 2's printed-shape and real-lens experiments before claiming a physical error budget.
