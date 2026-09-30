import pytest

from app.domain.entities import Detection, DetectionResult, ShapeType
from app.domain.value_objects import BoundingBox, DetectionScore, ImageSize, ScoreType


def detection(
    shape: ShapeType,
    score: float = 0.9,
    score_type: ScoreType = ScoreType.GEOMETRIC_SIMILARITY,
    bbox: BoundingBox | None = None,
) -> Detection:
    return Detection(
        shape=shape,
        bbox=bbox or BoundingBox(0, 0, 10, 10),
        score=DetectionScore(score, score_type),
    )


def test_empty_result_is_valid_and_summarised() -> None:
    result = DetectionResult(image_size=ImageSize(100, 100), detections=())

    assert result.summary.total == 0
    assert result.summary.classes == 0
    assert result.summary.by_class == {}
    assert result.summary.average_score is None
    assert result.summary.score_type is None


def test_summary_counts_classes_and_averages_scores() -> None:
    result = DetectionResult(
        image_size=ImageSize(100, 100),
        detections=(
            detection(ShapeType.SQUARE, 0.8),
            detection(ShapeType.CIRCLE, 0.9),
            detection(ShapeType.CIRCLE, 1.0),
        ),
    )

    summary = result.summary
    assert summary.total == 3
    assert summary.classes == 2
    # Keys follow ShapeType declaration order regardless of detection order.
    assert list(summary.by_class.items()) == [(ShapeType.CIRCLE, 2), (ShapeType.SQUARE, 1)]
    assert summary.average_score == pytest.approx(0.9)
    assert summary.score_type is ScoreType.GEOMETRIC_SIMILARITY


def test_summary_does_not_average_mixed_score_types() -> None:
    result = DetectionResult(
        image_size=ImageSize(100, 100),
        detections=(
            detection(ShapeType.SQUARE, 0.8, ScoreType.GEOMETRIC_SIMILARITY),
            detection(ShapeType.CIRCLE, 0.9, ScoreType.MODEL_CONFIDENCE),
        ),
    )

    assert result.summary.average_score is None
    assert result.summary.score_type is None


def test_rejects_boxes_outside_the_image() -> None:
    with pytest.raises(ValueError, match="exceeds image bounds"):
        DetectionResult(
            image_size=ImageSize(50, 50),
            detections=(detection(ShapeType.SQUARE, bbox=BoundingBox(40, 40, 60, 60)),),
        )
