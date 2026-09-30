"""Trace a detected shape's real boundary as a compact polygon.

The outline follows the contour that was classified, simplified with ``approxPolyDP`` to
within ``tolerance`` pixels. It keeps corners exactly where they are in the image
(sharp stays sharp, rounded stays rounded) and curves stay smooth, using a few dozen
points instead of hundreds. Tracing, rather than drawing an idealised shape, means the
outline never claims more precision than the image supports.
"""

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray


def trace_outline(contour: MatLike, tolerance: float) -> NDArray[np.float64] | None:
    """Outline points ``(N, 2)`` in the contour's coordinate space, or ``None``."""
    simplified = cv2.approxPolyDP(contour, tolerance, closed=True)
    points = simplified.reshape(-1, 2).astype(np.float64)
    return points if len(points) >= 3 else None
