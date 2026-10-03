"""Refine the coarse rim to the outer half-contrast crossing in the source intensities."""
import cv2
import numpy as np


def refine_outer_edge(points, rectified, resolution):
    previous, following = np.roll(points, 4, axis=0), np.roll(points, -4, axis=0)
    tangent = following - previous
    normals = np.column_stack([tangent[:, 1], -tangent[:, 0]])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-9)
    inward = np.sum(normals * (points - points.mean(axis=0)), axis=1) < 0
    normals[inward] *= -1
    distances = np.linspace(-1.0, 1.0, 81)
    coordinates = (points[:, None, :] + normals[:, None, :] * distances[None, :, None]) * resolution
    profile = cv2.remap(rectified, coordinates[:, :, 0].astype(np.float32),
                        coordinates[:, :, 1].astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REPLICATE).astype(float)
    bright = np.median(profile[:, distances >= 0.7], axis=1)
    minima = np.argmin(profile[:, distances <= 0.3], axis=1)
    dark = profile[np.arange(len(profile)), minima]
    thresholds = (bright + dark) / 2
    shifts = np.zeros(len(points))
    usable = np.zeros(len(points), dtype=bool)
    for index, minimum in enumerate(minima):
        if bright[index] - dark[index] < 15:
            continue
        crossings = np.flatnonzero((profile[index, minimum:-1] <= thresholds[index]) &
                                    (profile[index, minimum + 1:] > thresholds[index]))
        if not len(crossings):
            continue
        crossing = minimum + crossings[0]
        fraction = ((thresholds[index] - profile[index, crossing]) /
                    (profile[index, crossing + 1] - profile[index, crossing]))
        shifts[index] = distances[crossing] + fraction * (distances[1] - distances[0])
        usable[index] = True
    if usable.mean() < 0.9:
        raise ValueError("outer rim is unclear; improve the lighting and retake the photo")
    return points + normals * shifts[:, None], float(usable.mean())
