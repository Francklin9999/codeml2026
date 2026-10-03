import itertools
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon

WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK / "strat9"))
from frame import build_frame, generate, validate_mesh


TOLERANCES_MM = (0.01, 0.02, 0.03, 0.05)
DENSITIES = (96, 192, 384)
HOLDOUT_INDICES = frozenset((8, 9, 10, 11))


def radial_contour(index, count=1024):
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
    radial = (1 + 0.055 * np.cos(3 * angles + index * 0.19)
              + 0.025 * np.sin(5 * angles - index * 0.13)
              + 0.012 * np.cos(7 * angles + index * 0.07))
    width = 43 + index % 5 * 2.3
    height = 29 + index % 4 * 1.7
    coordinates = np.column_stack((width * radial * np.cos(angles) / 2,
                                   height * radial * np.sin(angles) / 2))
    return Polygon(coordinates)


def resample_polygon(polygon, count):
    points = np.asarray(polygon.exterior.coords[:-1], dtype=float)
    edge_lengths = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(edge_lengths)))
    distances = np.linspace(0, cumulative[-1], count, endpoint=False)
    closed = np.vstack((points, points[0]))
    sampled = np.column_stack([np.interp(distances, cumulative, closed[:, axis])
                               for axis in range(2)])
    return Polygon(sampled)


def geometry_metrics(reference, candidate, density):
    reference_bounds = reference.bounds
    candidate_bounds = candidate.bounds
    extent_drift = max(abs(reference_bounds[index] - candidate_bounds[index])
                       for index in range(4))
    return {
        "hausdorff_mm": float(reference.hausdorff_distance(candidate)),
        "extent_drift_mm": float(extent_drift),
        "perimeter_drift_mm": float(abs(reference.length - candidate.length)),
        "area_relative_drift": float(abs(reference.area - candidate.area) / reference.area),
        "vertex_reduction": float(1 - len(candidate.exterior.coords[:-1]) / density),
    }


def strategy21_experiment():
    shape_set = [radial_contour(index) for index in range(12)]
    development_indices = [index for index in range(12) if index not in HOLDOUT_INDICES]
    records = []
    for index, truth in enumerate(shape_set):
        for density, tolerance in itertools.product(DENSITIES, TOLERANCES_MM):
            reference = resample_polygon(truth, density)
            simplified = reference.simplify(tolerance, preserve_topology=True)
            records.append({"shape_index": index, "partition": "holdout" if index in HOLDOUT_INDICES else "development",
                            "density": density, "tolerance_mm": tolerance,
                            **geometry_metrics(reference, simplified, density)})

    candidate_rows = []
    for density, tolerance in itertools.product(DENSITIES, TOLERANCES_MM):
        development_rows = [record for record in records
                            if record["partition"] == "development"
                            and record["density"] == density
                            and record["tolerance_mm"] == tolerance]
        gate = all(row["hausdorff_mm"] <= 0.05 and row["extent_drift_mm"] <= 0.1
                   and row["vertex_reduction"] >= 0.3 for row in development_rows)
        candidate_rows.append({"density": density, "tolerance_mm": tolerance,
                               "development_gate": gate,
                               "mean_vertices_retained": 1 - float(np.mean(
                                   [row["vertex_reduction"] for row in development_rows]))})

    passing_candidates = [row for row in candidate_rows if row["development_gate"]]
    selected = (min(passing_candidates, key=lambda row: (row["mean_vertices_retained"],
                                                          row["density"], row["tolerance_mm"]))
                if passing_candidates else None)
    holdout_rows = []
    if selected is not None:
        holdout_rows = [record for record in records
                        if record["partition"] == "holdout"
                        and record["density"] == selected["density"]
                        and record["tolerance_mm"] == selected["tolerance_mm"]]

    negative_control = []
    for index in sorted(HOLDOUT_INDICES):
        reference = resample_polygon(shape_set[index], 192)
        simplified = reference.simplify(0.2, preserve_topology=True)
        negative_control.append({"shape_index": index, **geometry_metrics(reference, simplified, 192)})

    return {
        "shape_family": "deterministic radial Fourier contours, distinct from earlier ellipse family",
        "shapes": len(shape_set),
        "development_shapes": len(development_indices),
        "frozen_holdout_shapes": sorted(HOLDOUT_INDICES),
        "tested_candidates": len(candidate_rows),
        "candidate_grid": candidate_rows,
        "selected_development_setting": selected,
        "holdout_results": holdout_rows,
        "holdout_gate": bool(holdout_rows) and all(
            row["hausdorff_mm"] <= 0.05 and row["extent_drift_mm"] <= 0.1
            and row["vertex_reduction"] >= 0.3 for row in holdout_rows),
        "high_tolerance_negative_control_0_2mm": negative_control,
        "all_geometry_records": records,
        "scope": "simplification fidelity against the same resampled input polygon; no offsets or STL sections",
    }


def _frame_parameters(scale_factor=1.0):
    return {name: value * scale_factor for name, value in {
        "rim_width": 3.5, "thickness": 4.0, "clearance": 0.2, "lip": 0.5,
        "bridge_width": 18.0, "bridge_height": 7.0, "tenon_length": 4.0,
        "tenon_height": 6.0, "pin_diameter": 1.5}.items()}


def _mesh_summary(mesh):
    checks = validate_mesh(mesh)
    return {"checks": checks, "bounds": mesh.bounds.tolist(),
            "extents": mesh.extents.tolist(), "volume_mm3": float(mesh.volume)}


def strategy27_export_experiment():
    left_polygon = radial_contour(2, 128)
    right_polygon = radial_contour(7, 128)
    left_points = np.asarray(left_polygon.exterior.coords[:-1])
    right_points = np.asarray(right_polygon.exterior.coords[:-1])
    base = build_frame(left_points, right_points)
    shifted = build_frame(left_points + [17.3, -6.2], right_points + [17.3, -6.2])
    reflected_swapped = build_frame(right_points * [-1, 1], left_points * [-1, 1])
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        left_json = directory / "left.json"
        right_json = directory / "right.json"
        stl_path = directory / "frame.stl"
        left_json.write_text(json.dumps({"contour_mm": left_points.tolist()}), encoding="utf-8")
        right_json.write_text(json.dumps({"contour_mm": right_points.tolist()}), encoding="utf-8")
        base_metadata = generate(left_json, right_json, stl_path)
        reloaded = trimesh.load(stl_path, force="mesh")
        scale_sweep = []
        for factor in (0.8, 1.2, 1.5):
            scaled_left_json = directory / f"left_{factor}.json"
            scaled_right_json = directory / f"right_{factor}.json"
            scaled_stl_path = directory / f"frame_{factor}.stl"
            scaled_left_json.write_text(json.dumps({
                "contour_mm": (left_points * factor).tolist()}), encoding="utf-8")
            scaled_right_json.write_text(json.dumps({
                "contour_mm": (right_points * factor).tolist()}), encoding="utf-8")
            scaled_metadata = generate(scaled_left_json, scaled_right_json, scaled_stl_path,
                                       _frame_parameters(factor))
            scaled_reload = trimesh.load(scaled_stl_path, force="mesh")
            scale_sweep.append({
                "factor": factor,
                "dimension_drift_mm": float(np.max(np.abs(
                    scaled_reload.extents / factor - base.extents))),
                "bounds_drift_mm": float(np.max(np.abs(
                    scaled_reload.bounds / factor - base.bounds))),
                "volume_relative_drift": float(abs(
                    scaled_reload.volume / base.volume - factor ** 3) / factor ** 3),
                "generation_metadata": scaled_metadata,
                "reloaded_mesh": _mesh_summary(scaled_reload),
            })

    base_summary = _mesh_summary(base)
    reloaded_summary = _mesh_summary(reloaded)
    shifted_summary = _mesh_summary(shifted)
    reflected_summary = _mesh_summary(reflected_swapped)
    base_dimensions = np.asarray(base_summary["extents"])
    translated_dimension_drift = float(np.max(np.abs(base_dimensions - shifted_summary["extents"])))
    translated_volume_relative_drift = float(abs(base.volume - shifted.volume) / base.volume)
    reloaded_dimension_drift = float(np.max(np.abs(base_dimensions - reloaded_summary["extents"])))
    reloaded_volume_relative_drift = float(abs(base.volume - reloaded.volume) / base.volume)
    mirrored_dimension_drift = float(np.max(np.abs(base_dimensions - reflected_summary["extents"])))
    mirrored_volume_relative_drift = float(abs(base.volume - reflected_swapped.volume) / base.volume)
    scale_1_2 = next(record for record in scale_sweep if record["factor"] == 1.2)

    return {
        "base_mesh": base_summary,
        "stl_reloaded_mesh": reloaded_summary,
        "translated_input_mesh": shifted_summary,
        "reflected_and_swapped_mesh": reflected_summary,
        "scale_sweep": scale_sweep,
        "base_generation_metadata": base_metadata,
        "translation_dimension_drift_mm": translated_dimension_drift,
        "translation_volume_relative_drift": translated_volume_relative_drift,
        "stl_reload_dimension_drift_mm": reloaded_dimension_drift,
        "stl_reload_volume_relative_drift": reloaded_volume_relative_drift,
        "mirror_swap_dimension_drift_mm": mirrored_dimension_drift,
        "mirror_swap_volume_relative_drift": mirrored_volume_relative_drift,
        "scaled_dimension_drift_mm": scale_1_2["dimension_drift_mm"],
        "scaled_volume_relative_drift": scale_1_2["volume_relative_drift"],
        "left_right_orientation_metadata_available": False,
        "scope": "translation, reflection with eye swap, uniform scaling with all geometric parameters scaled, and STL reload",
    }


if __name__ == "__main__":
    result = {"strategy21": strategy21_experiment(),
              "strategy27": strategy27_export_experiment()}
    output = Path(__file__).with_name("_local") / "experiment_results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    strategy21 = result["strategy21"]
    summary = {
        "strategy21_selected_development_setting": strategy21["selected_development_setting"],
        "strategy21_holdout_gate": strategy21["holdout_gate"],
        "strategy21_holdout_results": strategy21["holdout_results"],
        "strategy21_negative_control": strategy21["high_tolerance_negative_control_0_2mm"],
        "strategy27": {key: value for key, value in result["strategy27"].items()
                       if key.endswith("drift") or key.endswith("drift_mm")
                       or key.endswith("available")},
    }
    print(json.dumps(summary, indent=2))
