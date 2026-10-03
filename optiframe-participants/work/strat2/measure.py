"""Measure one backlit lens photo and export a metric contour and 1:1 SVG."""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

WORK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK / "strat3"))
from shared.geometry import LOCAL, SPEC_PATH, dimensions, load_spec, write_image
from strat2.homography import rectify
from strat2.edges import refine_outer_edge
from segment_classic import segment


def smooth_contour(points, samples=720, harmonics=30):
    lengths = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
    cumulative = np.concatenate([[0], np.cumsum(lengths)])
    positions = np.linspace(0, cumulative[-1], samples, endpoint=False)
    closed = np.vstack([points, points[0]])
    regular = np.column_stack([np.interp(positions, cumulative, closed[:, axis]) for axis in range(2)])
    spectrum = np.fft.rfft(regular, axis=0)
    spectrum[harmonics + 1:] = 0
    return np.fft.irfft(spectrum, n=samples, axis=0)


def parallax_correct(points, camera_distance_mm, edge_height_mm, nadir_mm):
    if not np.isfinite([camera_distance_mm, edge_height_mm, *nadir_mm]).all():
        raise ValueError("parallax inputs must be finite")
    if not 0 <= edge_height_mm < camera_distance_mm:
        raise ValueError("camera distance must exceed the nonnegative edge height")
    nadir = np.asarray(nadir_mm, dtype=float)
    return nadir + (points - nadir) * (camera_distance_mm - edge_height_mm) / camera_distance_mm


def write_svg(points, output):
    shifted = points - points.min(axis=0) + 3
    width, height = np.maximum(np.ptp(points, axis=0) + 6, [56, 0])
    path = "M " + " L ".join(f"{horizontal:.4f},{vertical:.4f}" for horizontal, vertical in shifted) + " Z"
    markup = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.4f}mm" '
              f'height="{height + 14:.4f}mm" viewBox="0 0 {width:.4f} {height + 14:.4f}">'
              f'<path d="{path}" fill="none" stroke="black" stroke-width="0.15"/>'
              f'<path d="M 3,{height + 5} h 50" stroke="black" stroke-width="0.2"/>'
              f'<text x="3" y="{height + 10}" font-size="2.6">50 mm - Print at 100%</text></svg>')
    Path(output).write_text(markup, encoding="utf-8")


def measure(image_path, output, spec_path=SPEC_PATH, camera_distance_mm=None, edge_height_mm=0, nadir_mm=None):
    spec = load_spec(spec_path)
    image = cv2.imread(str(image_path))
    rectified, _, calibration = rectify(image, spec)
    points, debug = segment(rectified, spec)
    points = smooth_contour(points)
    points, refined_fraction = refine_outer_edge(points, rectified, spec["pixels_per_mm"])
    points = smooth_contour(points)
    if edge_height_mm:
        if camera_distance_mm is None or nadir_mm is None:
            raise ValueError("height correction requires measured camera distance and board-plane nadir")
        points = parallax_correct(points, camera_distance_mm, edge_height_mm, nadir_mm)
    result = {"image": Path(image_path).name, **dimensions(points), "calibration": calibration,
              "edge_definition": "smoothed outer half-contrast crossing of the detected dark rim",
              "refined_fraction": refined_fraction,
              "horizontal_axis": "board horizontal; align the lens before capture",
              "edge_height_mm": edge_height_mm, "parallax_corrected": bool(edge_height_mm),
              "physically_validated": False, "contour_mm": points.tolist()}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_image(output / "rectified.png", rectified)
    for name, view in debug.items():
        write_image(output / f"{name}.png", view)
    overlay = cv2.cvtColor(rectified, cv2.COLOR_GRAY2BGR)
    cv2.polylines(overlay, [np.rint(points * spec["pixels_per_mm"]).astype(np.int32)], True, (0, 0, 255), 2)
    write_image(output / "contour_overlay.png", overlay)
    write_svg(points, output / "contour.svg")
    (output / "measurement.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, default=LOCAL / "measurement")
    parser.add_argument("--spec", type=Path, default=SPEC_PATH)
    parser.add_argument("--camera-distance-mm", type=float)
    parser.add_argument("--edge-height-mm", type=float, default=0)
    parser.add_argument("--nadir-mm", type=float, nargs=2)
    args = parser.parse_args()
    try:
        result = measure(args.image, args.output, args.spec, args.camera_distance_mm, args.edge_height_mm, args.nadir_mm)
    except (ValueError, OSError, cv2.error) as error:
        parser.exit(1, f"Cannot measure: {error}\n")
    print(json.dumps({key: value for key, value in result.items() if key != "contour_mm"}, indent=2))
