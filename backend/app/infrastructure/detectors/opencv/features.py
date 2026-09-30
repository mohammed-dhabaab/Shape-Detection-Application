"""Translate an OpenCV contour into the domain's scale-invariant ``ShapeFeatures``."""

import math

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray

from app.domain.services import ShapeFeatures

# Outlines are resampled to evenly spaced points before ellipse fitting, so long straight
# edges (stored as just two points by CHAIN_APPROX_SIMPLE) carry their proper weight.
_ELLIPSE_SAMPLE_POINTS = 128


def measure_contour(contour: MatLike, approximation_factor: float) -> ShapeFeatures | None:
    """Measure a closed contour. Returns ``None`` for degenerate contours."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, closed=True)
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    if area <= 0 or perimeter <= 0 or hull_area <= 0:
        return None

    polygon = cv2.approxPolyDP(contour, approximation_factor * perimeter, closed=True)
    polygon_area = cv2.contourArea(polygon)
    _, (rect_width, rect_height), _ = cv2.minAreaRect(contour)
    _, radius = cv2.minEnclosingCircle(contour)
    long_side = max(rect_width, rect_height)

    return ShapeFeatures(
        vertex_count=len(polygon),
        circularity=4 * math.pi * area / perimeter**2,
        solidity=area / hull_area,
        aspect_ratio=min(rect_width, rect_height) / long_side if long_side else 0.0,
        polygon_fit=1.0 - abs(area - polygon_area) / area,
        enclosing_circle_fill=area / (math.pi * radius**2) if radius else 0.0,
        ellipse_fit=ellipse_fit(contour),
        interior_angles=interior_angles(polygon.reshape(-1, 2).astype(np.float64)),
    )


def ellipse_fit(contour: MatLike) -> float:
    """``1 - mean relative radial deviation`` of the outline from its best-fit ellipse.

    Each outline point is expressed in the fitted ellipse's normalised frame, where the
    ellipse is the unit circle; a point's radius there is 1.0 exactly on the ellipse.
    """
    points = resample_outline(contour.reshape(-1, 2).astype(np.float64), _ELLIPSE_SAMPLE_POINTS)
    if len(points) < 5:
        return 0.0
    (centre_x, centre_y), (width, height), angle = cv2.fitEllipse(points.astype(np.float32))
    if width <= 0 or height <= 0:
        return 0.0
    theta = math.radians(angle)
    dx, dy = points[:, 0] - centre_x, points[:, 1] - centre_y
    along = dx * math.cos(theta) + dy * math.sin(theta)
    across = -dx * math.sin(theta) + dy * math.cos(theta)
    radii = np.hypot(along / (width / 2), across / (height / 2))
    return max(0.0, 1.0 - float(np.mean(np.abs(radii - 1.0))))


def resample_outline(points: NDArray[np.float64], count: int) -> NDArray[np.float64]:
    """``count`` points evenly spaced by arc length along a closed polyline."""
    closed = np.vstack([points, points[:1]])
    cumulative = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(closed, axis=0), axis=1))])
    if cumulative[-1] == 0:
        return points[:0]
    positions = np.linspace(0.0, cumulative[-1], count, endpoint=False)
    return np.stack(
        [
            np.interp(positions, cumulative, closed[:, 0]),
            np.interp(positions, cumulative, closed[:, 1]),
        ],
        axis=1,
    )


def interior_angles(vertices: NDArray[np.float64]) -> tuple[float, ...]:
    """Interior angles (degrees) at each vertex of a simple convex polygon."""
    count = len(vertices)
    if count < 3:
        return ()
    angles: list[float] = []
    for index in range(count):
        current = vertices[index]
        to_previous = vertices[index - 1] - current
        to_next = vertices[(index + 1) % count] - current
        norms = float(np.linalg.norm(to_previous) * np.linalg.norm(to_next))
        if norms == 0:
            return ()
        cosine = float(np.dot(to_previous, to_next)) / norms
        angles.append(math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
    return tuple(angles)
