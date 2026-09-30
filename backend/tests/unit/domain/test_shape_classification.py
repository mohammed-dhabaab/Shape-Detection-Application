from dataclasses import replace

import pytest

from app.domain.entities import ShapeType
from app.domain.services import ClassificationRules, ShapeClassifier, ShapeFeatures

classifier = ShapeClassifier(ClassificationRules())


def polygon(vertex_count: int, angle: float, **overrides: float) -> ShapeFeatures:
    """Features of a clean, regular polygon; override individual measurements."""
    features = ShapeFeatures(
        vertex_count=vertex_count,
        circularity=0.75,
        solidity=1.0,
        aspect_ratio=1.0,
        polygon_fit=1.0,
        enclosing_circle_fill=0.6,
        ellipse_fit=0.9,
        interior_angles=(angle,) * vertex_count,
    )
    return replace(features, **overrides)


CIRCLE = ShapeFeatures(
    vertex_count=8,
    circularity=0.9,
    solidity=0.99,
    aspect_ratio=1.0,
    polygon_fit=0.9,
    enclosing_circle_fill=0.97,
    ellipse_fit=0.998,
    interior_angles=(135.0,) * 8,
)

# An oval with axis ratio ~0.6: a near-perfect ellipse that fills little of its
# enclosing circle.
ELLIPSE = replace(CIRCLE, circularity=0.93, aspect_ratio=0.6, enclosing_circle_fill=0.6)


@pytest.mark.parametrize(
    ("features", "expected"),
    [
        (CIRCLE, ShapeType.CIRCLE),
        (ELLIPSE, ShapeType.ELLIPSE),
        (polygon(3, 60), ShapeType.TRIANGLE),
        (polygon(4, 90), ShapeType.SQUARE),
        (polygon(4, 90, aspect_ratio=0.5), ShapeType.RECTANGLE),
        (polygon(5, 108), ShapeType.PENTAGON),
        (polygon(6, 120, enclosing_circle_fill=0.83, circularity=0.9), ShapeType.HEXAGON),
    ],
)
def test_classifies_clean_shapes(features: ShapeFeatures, expected: ShapeType) -> None:
    classification = classifier.classify(features)

    assert classification is not None
    assert classification.shape is expected
    assert classification.similarity >= 0.9


def test_circle_takes_precedence_over_vertex_count() -> None:
    """Polygon approximation of a circle yields arbitrary vertex counts (here 6)."""
    classification = classifier.classify(replace(CIRCLE, vertex_count=6))

    assert classification is not None
    assert classification.shape is ShapeType.CIRCLE


def test_hexagon_is_not_mistaken_for_circle() -> None:
    # A regular hexagon is fairly circular but fills only ~83% of its enclosing circle.
    hexagon = polygon(6, 120, circularity=0.9, enclosing_circle_fill=0.83)

    classification = classifier.classify(hexagon)

    assert classification is not None
    assert classification.shape is ShapeType.HEXAGON


def test_hexagon_beats_ellipse_when_its_polygon_match_is_better() -> None:
    # Regular hexagons are fairly elliptical (fit ~0.96) but match a hexagon better.
    hexagon = polygon(6, 120, circularity=0.9, enclosing_circle_fill=0.83, ellipse_fit=0.96)

    classification = classifier.classify(hexagon)

    assert classification is not None
    assert classification.shape is ShapeType.HEXAGON


def test_octagon_is_not_mistaken_for_circle() -> None:
    # A regular octagon fills its enclosing circle like a circle does (~0.90) but its
    # outline deviates measurably from an ellipse (fit ~0.979).
    octagon = replace(CIRCLE, enclosing_circle_fill=0.9, ellipse_fit=0.979)

    assert classifier.classify(octagon) is None


def test_ellipse_similarity_reflects_fit_quality() -> None:
    classification = classifier.classify(replace(ELLIPSE, ellipse_fit=0.99))

    assert classification is not None
    assert classification.similarity == pytest.approx(0.99 * ELLIPSE.solidity)


def test_square_tolerance_boundary() -> None:
    rules = ClassificationRules(square_aspect_ratio_tolerance=0.1)
    strict = ShapeClassifier(rules)

    near_square = strict.classify(polygon(4, 90, aspect_ratio=0.92))
    elongated = strict.classify(polygon(4, 90, aspect_ratio=0.85))

    assert near_square is not None
    assert near_square.shape is ShapeType.SQUARE
    assert elongated is not None
    assert elongated.shape is ShapeType.RECTANGLE


@pytest.mark.parametrize(
    ("features", "reason"),
    [
        (polygon(4, 90, solidity=0.6), "concave contours are not supported shapes"),
        (polygon(7, 128.6), "heptagons are not supported"),
        (polygon(2, 0), "degenerate polygon"),
        (polygon(4, 90, polygon_fit=0.5), "poor polygon fit scores below threshold"),
        (polygon(4, 90, interior_angles=(50.0, 130.0, 50.0, 130.0)), "rhombus is not a rectangle"),
    ],
)
def test_rejects_unsupported_or_low_quality_contours(features: ShapeFeatures, reason: str) -> None:
    assert classifier.classify(features) is None, reason


def test_similarity_reflects_angle_regularity() -> None:
    regular = classifier.classify(polygon(5, 108))
    irregular = classifier.classify(
        polygon(5, 108, interior_angles=(100.0, 116.0, 100.0, 116.0, 108.0))
    )

    assert regular is not None
    assert irregular is not None
    assert irregular.similarity < regular.similarity


def test_min_score_is_configurable() -> None:
    lenient = ShapeClassifier(ClassificationRules(min_score=0.4))

    classification = lenient.classify(polygon(4, 90, polygon_fit=0.5))

    assert classification is not None
    assert classification.shape is ShapeType.SQUARE
