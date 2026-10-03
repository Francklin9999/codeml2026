# Parametric frame front prototype

`frame.py` reads `contour_mm` arrays written by `work/strat2/measure.py` and writes a binary STL. Each JSON contains one lens. Orient inputs in frame coordinates: the left lens nasal edge points toward +x and the right nasal edge toward -x. The generator aligns those nasal boxing edges to the requested bridge width (DBL) and recenters each contour vertically by its boxing midpoint, so board-coordinate measurement files work directly. The contours can have different shapes and widths.

The frame uses a layered opening: front and back lips reduce the opening by `lip`, while the middle groove uses the measured contour plus `clearance`. The bridge overlaps the nasal rims while subtracting both lens seats, preserving the openings. Defaults are in `frame.py`; override them with a JSON file, for example `{"bridge_width": 18, "clearance": 0.2}`. Temporal tenons include transverse pin bores. Dependencies are Shapely 2.1 or later, trimesh 5, and manifold3d.

Run:

```powershell
python frame.py left/measurement.json right/measurement.json frame.stl
python -m unittest test_frame.py
```

The CLI rejects invalid contours and parameters, then verifies watertightness, consistent winding, positive volume, one connected body, and nondegenerate faces before export. Tests include two different lens outlines, board-offset measurement JSON via CLI, sampled lens openings at the midplane, protruding tenons, and invalid inputs. The prototype does not validate lens fit, hinge compatibility, slicer acceptance, or physical strength. Inspect STL in a slicer and test printed samples before use.
