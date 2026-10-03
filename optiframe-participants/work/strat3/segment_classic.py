"""Classical dark-rim baseline restricted to the metric lens window."""
import cv2
import numpy as np


def kernel(diameter_mm, resolution):
    diameter = max(3, round(diameter_mm * resolution) | 1)
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (diameter, diameter))


def segment(rectified, spec):
    resolution = spec["pixels_per_mm"]
    left, top, right, bottom = spec["window_mm"]
    origin = np.rint(np.array([left, top]) * resolution).astype(int)
    window = rectified[origin[1]:round(bottom * resolution), origin[0]:round(right * resolution)]
    background = cv2.GaussianBlur(window.astype(np.float32), (0, 0), 2.5 * resolution)
    normalized = np.clip(window.astype(np.float32) / np.maximum(background, 1) * 230, 0, 255).astype(np.uint8)
    enhanced = cv2.morphologyEx(normalized, cv2.MORPH_BLACKHAT, kernel(1.5, resolution))
    _, rim = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if float(enhanced.max()) < 15:
        raise ValueError("lens rim has insufficient contrast; improve backlighting")
    closed = cv2.morphologyEx(rim, cv2.MORPH_CLOSE, kernel(0.6, resolution))
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    candidates = []
    for contour in contours:
        area = cv2.contourArea(contour) / resolution ** 2
        left_px, top_px, width, height = cv2.boundingRect(contour)
        if left_px <= 2 or top_px <= 2 or left_px + width >= window.shape[1] - 2 or top_px + height >= window.shape[0] - 2:
            continue
        if not (600 <= area <= 4000 and 30 <= width / resolution <= 75 and 15 <= height / resolution <= 60):
            continue
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        if hull_area <= 0 or cv2.contourArea(contour) / hull_area < 0.9:
            continue
        candidates.append((area, contour))
    if len(candidates) != 1:
        raise ValueError(f"expected one complete lens in the window, found {len(candidates)}; recenter and retake")
    contour = candidates[0][1].reshape(-1, 2).astype(float)
    mask = np.zeros_like(window)
    cv2.drawContours(mask, [contour.astype(np.int32)], -1, 255, cv2.FILLED)
    points = (contour + origin) / resolution
    return points, {"window": window, "normalized": normalized, "enhanced": enhanced, "mask": mask}
