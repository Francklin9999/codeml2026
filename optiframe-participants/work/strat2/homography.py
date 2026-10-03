"""Detect the ChArUco frame and rectify to board-plane millimetres."""
import cv2
import numpy as np

from shared.geometry import board_size, make_board


def rectify(image, spec):
    if image is None or image.ndim not in (2, 3):
        raise ValueError("photo could not be read")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    board, _ = make_board(spec)
    parameters = cv2.aruco.DetectorParameters()
    parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    detector = cv2.aruco.CharucoDetector(board, detectorParams=parameters)
    corners, identifiers, _, _ = detector.detectBoard(gray)
    minimum = spec["minimum_charuco_corners"]
    if identifiers is None or len(identifiers) < minimum:
        count = 0 if identifiers is None else len(identifiers)
        raise ValueError(f"only {count} calibration corners; show the entire board (need {minimum})")
    source = corners.reshape(-1, 2).astype(np.float64)
    target = board.getChessboardCorners()[identifiers.ravel(), :2].astype(np.float64)
    left, top, right, bottom = spec["window_mm"]
    visible = ~((target[:, 0] >= left) & (target[:, 0] <= right) &
                (target[:, 1] >= top) & (target[:, 1] <= bottom))
    source, target = source[visible], target[visible]
    if len(source) < minimum:
        raise ValueError("too few calibration corners outside the cut-out window")
    homography, inliers = cv2.findHomography(source, target, cv2.RANSAC, 0.25)
    if homography is None or inliers is None or inliers.sum() < minimum:
        raise ValueError("calibration is inconsistent; flatten the board and retake the photo")
    keep = inliers.ravel().astype(bool)
    source, target = source[keep], target[keep]
    width, height = board_size(spec)
    quadrants = (target[:, 0] > width / 2).astype(int) + 2 * (target[:, 1] > height / 2).astype(int)
    if len(np.unique(quadrants)) < 4:
        raise ValueError("calibration must surround the lens in all four board quadrants")
    homography, _ = cv2.findHomography(source, target, 0)
    projected = cv2.perspectiveTransform(source[:, None, :], homography).reshape(-1, 2)
    residual_mm = float(np.sqrt(np.mean(np.sum((projected - target) ** 2, axis=1))))
    projected_image = cv2.perspectiveTransform(target[:, None, :], np.linalg.inv(homography)).reshape(-1, 2)
    residual_px = float(np.sqrt(np.mean(np.sum((projected_image - source) ** 2, axis=1))))
    if residual_mm > spec["maximum_reprojection_mm"]:
        raise ValueError(f"calibration residual {residual_mm:.3f} mm exceeds the quality limit")
    resolution = spec["pixels_per_mm"]
    transform = np.diag([resolution, resolution, 1.0]) @ homography
    rectified = cv2.warpPerspective(gray, transform, (round(width * resolution), round(height * resolution)),
                                     flags=cv2.INTER_LANCZOS4, borderValue=255)
    details = {"corners": int(keep.sum()), "reprojection_mm": residual_mm,
               "reprojection_px": residual_px, "pixels_per_mm": resolution}
    return rectified, homography, details
