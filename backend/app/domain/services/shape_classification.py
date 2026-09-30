"""Rule-based shape classification from measured contour geometry.

This module is deliberately free of OpenCV: it reasons about *measurements* (vertex
count, circularity, angles, ...) that any contour-extraction backend can provide.
Keeping the rules here makes them unit-testable without images and keeps the
infrastructure adapter focused on pixel processing.
"""

from dataclasses import dataclass
from statistics import fmean

from app.domain.entities.shape import ShapeType

_IDEAL_INTERIOR_ANGLE: dict[int, float] = {
    vertices: 180.0 * (vertices - 2) / vertices for vertices in (4, 5, 6)
}


@dataclass(frozen=True, slots=True)
class ShapeFeatures:
    """Scale-invariant measurements of a single closed contour.

    Attributes:
        vertex_count: Vertices of the simplified (approximated) polygon.
        circularity: ``4πA / P²``; 1.0 for a perfect circle.
        solidity: Contour area divided by its convex hull area; 1.0 when convex.
        aspect_ratio: Short side / long side of the minimum-area (rotated) rectangle.
        polygon_fit: Area agreement between the contour and its approximated polygon.
        enclosing_circle_fill: Contour area divided by its minimum enclosing circle area.
        ellipse_fit: ``1 - mean relative radial deviation`` of the outline from its
            best-fit ellipse; 1.0 for a perfect ellipse (or circle).
        interior_angles: Interior angles of the approximated polygon, in degrees.
    """

    vertex_count: int
    circularity: float
    solidity: float
    aspect_ratio: float
    polygon_fit: float
    enclosing_circle_fill: float
    ellipse_fit: float
    interior_angles: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ClassificationRules:
    """Tunable thresholds for :class:`ShapeClassifier`.

    Attributes:
        min_solidity: Contours less convex than this are rejected (not a supported shape).
        circle_min_circularity: Minimum circularity for a contour to be a circle.
        circle_min_enclosing_fill: Minimum fill of the enclosing circle for a circle.
            A regular hexagon fills ~0.83 of it, a true circle ~1.0. Round outlines
            below this are ellipses.
        ellipse_min_fit: Minimum ``ellipse_fit`` for a round shape (circle or ellipse).
            True ellipses measure >= 0.99; regular polygons at most ~0.98 (octagon).
        square_aspect_ratio_tolerance: A quadrilateral whose rotated aspect ratio is
            within this tolerance of 1.0 is a square rather than a rectangle.
        min_score: Classifications scoring below this are discarded.
    """

    min_solidity: float = 0.9
    circle_min_circularity: float = 0.8
    circle_min_enclosing_fill: float = 0.88
    ellipse_min_fit: float = 0.985
    square_aspect_ratio_tolerance: float = 0.1
    min_score: float = 0.8


@dataclass(frozen=True, slots=True)
class Classification:
    shape: ShapeType
    similarity: float
    """How closely the contour matches the ideal form of ``shape``, in ``[0, 1]``."""


class ShapeClassifier:
    """Maps contour measurements to a supported shape and a geometric similarity."""

    def __init__(self, rules: ClassificationRules) -> None:
        self._rules = rules

    def classify(self, features: ShapeFeatures) -> Classification | None:
        if features.solidity < self._rules.min_solidity:
            return None

        # Round and polygonal interpretations are scored independently and the better
        # match wins: polygon approximation of a curve yields an arbitrary 5-8 vertices,
        # so vertex counting alone can't tell an ellipse from a hexagon.
        candidates = (self._classify_round(features), self._classify_polygon(features))
        best = max(
            (candidate for candidate in candidates if candidate is not None),
            key=lambda candidate: candidate.similarity,
            default=None,
        )
        if best is None or best.similarity < self._rules.min_score:
            return None
        return best

    def _classify_round(self, features: ShapeFeatures) -> Classification | None:
        if features.ellipse_fit < self._rules.ellipse_min_fit:
            return None
        is_circle = (
            features.circularity >= self._rules.circle_min_circularity
            and features.enclosing_circle_fill >= self._rules.circle_min_enclosing_fill
        )
        if is_circle:
            similarity = _clamp(features.enclosing_circle_fill) * features.solidity
            return Classification(ShapeType.CIRCLE, similarity)
        return Classification(ShapeType.ELLIPSE, _clamp(features.ellipse_fit) * features.solidity)

    def _classify_polygon(self, features: ShapeFeatures) -> Classification | None:
        base = _clamp(features.polygon_fit) * features.solidity
        match features.vertex_count:
            case 3:
                return Classification(ShapeType.TRIANGLE, base)
            case 4:
                return self._classify_quadrilateral(features, base)
            case 5:
                return Classification(ShapeType.PENTAGON, base * _angle_regularity(features))
            case 6:
                return Classification(ShapeType.HEXAGON, base * _angle_regularity(features))
            case _:
                return None

    def _classify_quadrilateral(self, features: ShapeFeatures, base: float) -> Classification:
        similarity = base * _angle_regularity(features)
        if features.aspect_ratio >= 1.0 - self._rules.square_aspect_ratio_tolerance:
            return Classification(ShapeType.SQUARE, similarity * features.aspect_ratio)
        return Classification(ShapeType.RECTANGLE, similarity)


def _angle_regularity(features: ShapeFeatures) -> float:
    """1.0 when every interior angle equals the regular polygon's angle."""
    ideal = _IDEAL_INTERIOR_ANGLE[features.vertex_count]
    if not features.interior_angles:
        return 0.0
    mean_deviation = fmean(abs(angle - ideal) for angle in features.interior_angles)
    return _clamp(1.0 - mean_deviation / ideal)


def _clamp(value: float) -> float:
    return min(max(value, 0.0), 1.0)
