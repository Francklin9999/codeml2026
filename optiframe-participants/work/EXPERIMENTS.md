# Reproduce the geometry and grouping checks

Run from the repository root with the existing NumPy, Shapely, trimesh, manifold and PyMuPDF environment:

```powershell
.\.venv\Scripts\python.exe optiframe-participants/work/strat21/geometry_experiments.py
.\.venv\Scripts\python.exe dayone-participants/work/strat21/grouped_split.py
```

The parent independently reproduced both runs. On four radial-contour holdouts, the development-selected 384-point / 0.05 mm simplification had maximum Hausdorff error **0.04824 mm** and vertex reduction **83.85–84.38%**. This tests simplification against its resampled input, not total measurement, sampling, offset or STL-section fidelity.

Metamorphic testing found fixed internal attachment margins that did not scale with frame parameters. Making those margins proportional to rim width preserves the default geometry. At scale factors 0.8, 1.2 and 1.5, the maximum normalized bounds drift is **3.82e-6 mm** and volume drift **4.08e-8 relative**. STL reload, translation and mirror/swap checks pass for the tested pair. Eye-side orientation metadata, the full contour suite, physical printing and fit remain unvalidated.

DayOne has 124 PNGs, 80 distinct hashes and 44 redundant copies. Only **38/80** pages can be linked using the automatic identity fingerprints, so no verified patient split or holdout is emitted. Cross-page/group hash collisions also block a split artifact even when the header check passes. Review the missing group links locally; do not infer that filename order alone validates identity.

Focused tests: 10 existing DayOne evaluator, 6 DayOne grouping/audit, 6 metrology, 7 frame and 2 geometry-experiment tests. Run `python -m unittest discover -s <folder> -p 'test_*.py' -v` for `dayone-participants/work/shared/tests`, `dayone-participants/work/strat21`, `optiframe-participants/work`, `optiframe-participants/work/strat9` and `optiframe-participants/work/strat21` separately. Generated results remain ignored; matrices distinguish these partial checks from unrun full adoption experiments.
