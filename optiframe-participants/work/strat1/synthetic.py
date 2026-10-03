"""Generate seeded, labelled pinhole-camera photos of idealised backlit lenses."""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.geometry import LOCAL, board_image, board_size, dimensions, lens_contour, load_spec, write_image


def projection(spec, tilt_x, tilt_y, distance=400, focal=2400, width=1400, height=1200, edge_height=0):
    horizontal, vertical = np.radians([tilt_x, tilt_y])
    rotation_x = np.array([[1, 0, 0], [0, np.cos(horizontal), -np.sin(horizontal)],
                           [0, np.sin(horizontal), np.cos(horizontal)]])
    rotation_y = np.array([[np.cos(vertical), 0, np.sin(vertical)], [0, 1, 0],
                           [-np.sin(vertical), 0, np.cos(vertical)]])
    rotation = rotation_y @ rotation_x
    center = board_size(spec) / 2
    offset = np.array([0, 0, distance]) - rotation @ np.array([*center, edge_height])
    intrinsics = np.array([[focal, 0, width / 2], [0, focal, height / 2], [0, 0, 1]])
    return intrinsics @ np.column_stack([rotation[:, 0], rotation[:, 1], offset])


def generate_case(output, name, width=55, height=40, shape="oval", tilt_x=0, tilt_y=0,
                  blur=0.5, noise=1, contrast=150, tint=0, edge_height=0, seed=42,
                  lens_present=True, markers_present=True):
    spec = load_spec()
    resolution = 20
    base = board_image(spec, resolution) if markers_present else np.full_like(board_image(spec, resolution), 255)
    plane_homography = projection(spec, tilt_x, tilt_y)
    lens_homography = projection(spec, tilt_x, tilt_y, edge_height=edge_height)
    transform = plane_homography @ np.diag([1 / resolution, 1 / resolution, 1])
    photo = cv2.warpPerspective(base, transform, (1400, 1200), flags=cv2.INTER_CUBIC, borderValue=235)
    contour = lens_contour(width, height, shape) + board_size(spec) / 2
    tangent = np.roll(contour, -1, axis=0) - np.roll(contour, 1, axis=0)
    normals = np.column_stack([tangent[:, 1], -tangent[:, 0]])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    ground_truth = contour + 0.25 * normals
    if lens_present:
        sheet = np.full(base.shape, 255, dtype=np.uint8)
        outer = np.rint(ground_truth * resolution).astype(np.int32)
        inner = np.rint((contour - 0.25 * normals) * resolution).astype(np.int32)
        cv2.fillPoly(sheet, [outer], 255 - contrast, lineType=cv2.LINE_AA)
        cv2.fillPoly(sheet, [inner], 255 - tint, lineType=cv2.LINE_AA)
        lens_transform = lens_homography @ np.diag([1 / resolution, 1 / resolution, 1])
        rim = cv2.warpPerspective(sheet, lens_transform, (1400, 1200), flags=cv2.INTER_CUBIC, borderValue=255)
        photo = np.minimum(photo, rim)
    photo = photo.astype(float)
    gradient = np.linspace(0.86, 1, photo.shape[1])[None, :]
    photo *= gradient
    if blur > 0:
        photo = cv2.GaussianBlur(photo, (0, 0), blur)
    photo += np.random.default_rng(seed).normal(0, noise, photo.shape)
    photo = np.clip(photo, 0, 255).astype(np.uint8)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    write_image(output / f"{name}.png", photo)
    truth = {"case": name, "image": f"{name}.png", "synthetic": True,
             "lens_present": lens_present, "markers_present": markers_present,
             "tilt_x_deg": tilt_x, "tilt_y_deg": tilt_y, "blur_px": blur, "noise_sigma": noise,
             "rim_contrast": contrast, "tint": tint, "edge_height_mm": edge_height,
             "camera_distance_mm": 400, "shape": shape, "seed": seed,
             "measurement_plane": "outer extent of an ideal 0.5 mm dark stroke centred on the lens contour",
             "contour_mm": ground_truth.tolist(), **dimensions(ground_truth)}
    (output / f"{name}.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    return truth


def suite(output, seed=42):
    cases = []
    for index, shape in enumerate(["oval", "rounded_rectangle", "asymmetric"]):
        for shot, (tilt_x, tilt_y) in enumerate([(0, 0), (20, -15), (-25, 20)]):
            cases.append(generate_case(output, f"{shape}_{shot}", shape=shape,
                                        width=52 + index * 3, height=37 + index * 2,
                                        tilt_x=tilt_x, tilt_y=tilt_y, seed=seed + len(cases)))
    cases.append(generate_case(output, "tinted", tint=100, contrast=170, tilt_y=20, seed=seed + 10))
    cases.append(generate_case(output, "blurred", blur=1.5, noise=3, tilt_x=15, seed=seed + 11))
    cases.append(generate_case(output, "low_contrast", contrast=70, noise=3, seed=seed + 12))
    cases.append(generate_case(output, "raised_3mm", edge_height=3, seed=seed + 13))
    cases.append(generate_case(output, "empty_window", lens_present=False, seed=seed + 14))
    cases.append(generate_case(output, "missing_markers", markers_present=False, seed=seed + 15))
    (Path(output) / "manifest.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    return cases


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=LOCAL / "synthetic")
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    print(f"Generated {len(suite(arguments.output, arguments.seed))} synthetic cases in {arguments.output}")
