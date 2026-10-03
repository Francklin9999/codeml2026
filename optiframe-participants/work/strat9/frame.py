"""Generate a closed frame front STL from two measure.py JSON contours."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import trimesh
from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.validation import explain_validity


DEFAULTS = {"rim_width": 3.5, "thickness": 4.0, "clearance": 0.2,
            "lip": 0.5, "bridge_width": 18.0, "bridge_height": 7.0,
            "tenon_length": 4.0, "tenon_height": 6.0, "pin_diameter": 1.5}


def load_contour(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    points = data.get("contour_mm") if isinstance(data, dict) else data
    if points is None:
        raise ValueError(f"{path}: expected a contour_mm array")
    return np.asarray(points, dtype=float)


def contour_polygon(points, label):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
        raise ValueError(f"{label} contour must contain at least three finite 2D points")
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= 1e-6:
        raise ValueError(f"{label} contour is invalid: {explain_validity(polygon)}")
    if polygon.geom_type != "Polygon":
        raise ValueError(f"{label} contour must be one closed outer boundary")
    return polygon


def validate_params(params):
    if params is not None and not isinstance(params, dict):
        raise ValueError("parameters must be a JSON object")
    values = dict(DEFAULTS)
    overrides = params or {}
    unknown = set(overrides) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"unknown parameter(s): {', '.join(sorted(unknown))}")
    values.update(overrides)
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a positive finite number")
    if values["lip"] >= values["rim_width"]:
        raise ValueError("lip must be smaller than rim_width")
    if values["thickness"] <= 2 * values["lip"]:
        raise ValueError("thickness must exceed twice the lip height")
    if values["pin_diameter"] >= min(values["tenon_length"], values["tenon_height"], values["thickness"]):
        raise ValueError("pin_diameter must be smaller than the tenon dimensions")
    return values


def _extrude(polygon, height, z):
    mesh = trimesh.creation.extrude_polygon(polygon, height)
    mesh.apply_translation((0, 0, z))
    return mesh


def build_frame(left_points, right_points, params=None):
    """Build STL-ready geometry; nasal contour edges must face the bridge."""
    settings = validate_params(params)
    left = contour_polygon(left_points, "left")
    right = contour_polygon(right_points, "right")
    bridge_width = settings["bridge_width"]
    outer_offset = settings["clearance"] + settings["rim_width"]
    left_bounds = left.bounds
    right_bounds = right.bounds
    left = translate(left, xoff=-bridge_width / 2 - left_bounds[2],
                     yoff=-(left_bounds[1] + left_bounds[3]) / 2)
    right = translate(right, xoff=bridge_width / 2 - right_bounds[0],
                      yoff=-(right_bounds[1] + right_bounds[3]) / 2)

    meshes = []
    lip_height = settings["lip"]
    groove_height = settings["thickness"] - 2 * lip_height
    for contour in (left, right):
        outer = contour.buffer(outer_offset, join_style="round", quad_segs=8)
        lip_opening = contour.buffer(-settings["lip"], join_style="round", quad_segs=8)
        seat_opening = contour.buffer(settings["clearance"], join_style="round", quad_segs=8)
        if (min(outer.area, lip_opening.area, seat_opening.area) <= 1e-6
                or outer.geom_type != "Polygon" or lip_opening.geom_type != "Polygon"
                or seat_opening.geom_type != "Polygon"):
            raise ValueError("contour is too small for the requested rim and lens groove")
        front = outer.difference(lip_opening)
        groove = outer.difference(seat_opening)
        back = outer.difference(lip_opening)
        for region, layer_height, z_offset in ((front, lip_height, 0), (groove, groove_height, lip_height),
                                               (back, lip_height, settings["thickness"] - lip_height)):
            if region.geom_type == "Polygon":
                meshes.append(_extrude(region, layer_height, z_offset))
            elif region.geom_type == "MultiPolygon":
                meshes.extend(_extrude(part, layer_height, z_offset) for part in region.geoms if part.area > 1e-6)

    reach = outer_offset + 0.2
    bridge_bounds = (-bridge_width / 2 - reach, -settings["bridge_height"] / 2,
                     bridge_width / 2 + reach, settings["bridge_height"] / 2)
    bridge = box(*bridge_bounds).difference(left.buffer(settings["clearance"])).difference(
        right.buffer(settings["clearance"]))
    if bridge.geom_type == "Polygon":
        meshes.append(_extrude(bridge, settings["thickness"], 0))
    elif bridge.geom_type == "MultiPolygon":
        meshes.extend(_extrude(part, settings["thickness"], 0)
                      for part in bridge.geoms if part.area > 1e-6)

    for contour, side in ((left, -1), (right, 1)):
        contour_bounds = contour.bounds
        temporal_x = contour_bounds[0] if side < 0 else contour_bounds[2]
        tenon_center_x = temporal_x + side * (outer_offset + settings["tenon_length"] / 2 - 0.2)
        tenon_center_y = (contour_bounds[1] + contour_bounds[3]) / 2
        tenon = trimesh.creation.box(extents=(settings["tenon_length"], settings["tenon_height"], settings["thickness"]))
        tenon.apply_translation((tenon_center_x, tenon_center_y, settings["thickness"] / 2))
        bore = trimesh.creation.cylinder(radius=settings["pin_diameter"] / 2,
                                         height=settings["tenon_length"] + 0.4, sections=32)
        rotation = trimesh.geometry.align_vectors([0, 0, 1], [1, 0, 0])
        bore.apply_transform(rotation)
        bore.apply_translation((tenon_center_x, tenon_center_y, settings["thickness"] / 2))
        meshes.append(trimesh.boolean.difference([tenon, bore], engine="manifold"))

    mesh = trimesh.boolean.union(meshes, engine="manifold")
    if isinstance(mesh, list):
        mesh = trimesh.util.concatenate(mesh)
    mesh.process(validate=True)
    return mesh


def validate_mesh(mesh):
    checks = {"watertight": bool(mesh.is_watertight),
              "winding_consistent": bool(mesh.is_winding_consistent),
              "positive_volume": bool(mesh.volume > 0),
              "single_body": len(mesh.split(only_watertight=False)) == 1,
              "nondegenerate_faces": bool(len(mesh.faces) > 0 and np.all(mesh.area_faces > 1e-10))}
    if not all(checks.values()):
        raise ValueError(f"generated mesh failed validation: {checks}")
    return checks


def generate(left_json, right_json, output, params=None):
    mesh = build_frame(load_contour(left_json), load_contour(right_json), params)
    checks = validate_mesh(mesh)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    mesh.export(output, file_type="stl")
    return {"output": str(output), "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)), "volume_mm3": float(mesh.volume), **checks,
            "physical_fit_validated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path, help="measure.py measurement.json; nasal edge toward +x")
    parser.add_argument("right", type=Path, help="measure.py measurement.json; nasal edge toward -x")
    parser.add_argument("output", type=Path)
    parser.add_argument("--params", type=Path, help="JSON parameter overrides")
    args = parser.parse_args()
    try:
        overrides = json.loads(args.params.read_text(encoding="utf-8")) if args.params else None
        print(json.dumps(generate(args.left, args.right, args.output, overrides), indent=2))
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"Cannot generate frame: {error}\n")
