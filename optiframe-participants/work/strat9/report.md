# Strategy 9 audit — 2026-10-03

A lower-cost subagent implemented the Python frame prototype; the parent reviewed the source and independently ran tests and an end-to-end measurement-to-STL check.

Audit fixes: board-coordinate contours are vertically recentered; the bridge subtracts lens seats to avoid blocking apertures; tenons extend beyond the outer rims; unknown/nonfinite parameters and oversized pin bores are rejected; offsets that split or disappear are rejected; CLI input errors produce a useful message rather than a nonexistent exception-handler error.

Six focused tests pass, covering asymmetric shapes, alternate parameters, self-intersections, invalid configuration, offset measurement JSON through the CLI, STL reload, cavity points 1–3 mm inward from each nasal edge, tenon protrusion and missing-input error handling.

Using the actual strategy-2 `oval_1` and `rounded_rectangle_1` measurement JSONs, the generated STL had 20,928 vertices, 41,860 faces and volume 5,339.3656 mm³. Watertightness, winding consistency, positive volume, single connected body and nondegenerate-face checks all passed. The measurements feeding that test are synthetic.

This is a Python prototype, not the planned JavaScript/browser generator. The physical groove fit, hinge compatibility, strength, slicer acceptance and printing tests are NOT RUN. Canonical anatomical orientation is still required from the caller. Strategy 9 remains IN PROGRESS.
