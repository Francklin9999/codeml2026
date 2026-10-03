"""Metric board geometry shared by capture, simulation and measurement."""
import json
from pathlib import Path

import cv2
import numpy as np


WORK = Path(__file__).resolve().parents[1]
SPEC_PATH = WORK / "strat1" / "board_spec.json"
LOCAL = WORK / "_local"


def load_spec(path=SPEC_PATH):
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    if spec["square_mm"] <= spec["marker_mm"] or spec["marker_mm"] <= 0:
        raise ValueError("board must have positive markers smaller than its squares")
    return spec


def make_board(spec):
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, spec["dictionary"]))
    board = cv2.aruco.CharucoBoard(tuple(spec["squares"]), spec["square_mm"], spec["marker_mm"], dictionary)
    return board, dictionary


def board_size(spec):
    return np.asarray(spec["squares"], dtype=float) * spec["square_mm"]


def board_image(spec, pixels_per_mm=10):
    board, _ = make_board(spec)
    width, height = board_size(spec)
    image = board.generateImage((round(width * pixels_per_mm), round(height * pixels_per_mm)),
                                marginSize=0, borderBits=1)
    left, top, right, bottom = spec["window_mm"]
    image[round(top * pixels_per_mm):round(bottom * pixels_per_mm),
          round(left * pixels_per_mm):round(right * pixels_per_mm)] = 255
    return image


def lens_contour(width, height, shape="oval", samples=720):
    angles = np.linspace(0, 2 * np.pi, samples, endpoint=False)
    if shape == "rounded_rectangle":
        horizontal = np.sign(np.cos(angles)) * np.abs(np.cos(angles)) ** 0.55
        vertical = np.sign(np.sin(angles)) * np.abs(np.sin(angles)) ** 0.55
    elif shape == "oval":
        horizontal, vertical = np.cos(angles), np.sin(angles)
    elif shape == "asymmetric":
        horizontal = np.cos(angles)
        vertical = np.sin(angles) * (1 + 0.12 * np.cos(angles))
    else:
        raise ValueError(f"unknown lens shape {shape}")
    points = np.column_stack([horizontal, vertical])
    points -= (points.max(axis=0) + points.min(axis=0)) / 2
    points *= np.array([width, height]) / np.ptp(points, axis=0)
    return points


def dimensions(points):
    points = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(points) < 3 or not np.isfinite(points).all():
        raise ValueError("contour must contain at least three finite points")
    width, height = np.ptp(points, axis=0)
    perimeter = np.linalg.norm(points - np.roll(points, 1, axis=0), axis=1).sum()
    return {"A_mm": float(width), "B_mm": float(height), "perimeter_mm": float(perimeter)}


def write_image(path, image):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise OSError(f"cannot write image {path}")
