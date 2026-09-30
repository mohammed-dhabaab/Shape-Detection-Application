"""Translate an OpenCV contour into the domain's scale-invariant ``ShapeFeatures``."""

import math

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray

from app.domain.services import ShapeFeatures


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
        interior_angles=interior_angles(polygon.reshape(-1, 2).astype(np.float64)),
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
