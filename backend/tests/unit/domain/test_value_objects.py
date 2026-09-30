import pytest

from app.domain.value_objects import BoundingBox, DetectionScore, ImageSize, ScoreType


class TestBoundingBox:
    def test_exposes_derived_dimensions(self) -> None:
        box = BoundingBox(x1=10, y1=20, x2=110, y2=70)

        assert (box.width, box.height, box.area) == (100, 50, 5000)

    @pytest.mark.parametrize(
        ("x1", "y1", "x2", "y2"),
        [(-1, 0, 10, 10), (0, -1, 10, 10), (10, 0, 10, 10), (0, 10, 10, 5)],
    )
    def test_rejects_invalid_coordinates(self, x1: int, y1: int, x2: int, y2: int) -> None:
        with pytest.raises(ValueError, match="Bounding box"):
            BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)

    def test_enclosing_box_contains_both(self) -> None:
        merged = BoundingBox(0, 5, 10, 10).enclosing(BoundingBox(5, 0, 20, 8))

        assert merged == BoundingBox(0, 0, 20, 10)

    def test_iou_of_identical_boxes_is_one(self) -> None:
        box = BoundingBox(0, 0, 10, 10)

        assert box.iou(box) == 1.0

    def test_iou_of_disjoint_boxes_is_zero(self) -> None:
        assert BoundingBox(0, 0, 10, 10).iou(BoundingBox(20, 20, 30, 30)) == 0.0

    def test_iou_of_partial_overlap(self) -> None:
        # Overlap 5x10 = 50; union = 100 + 100 - 50 = 150.
        assert BoundingBox(0, 0, 10, 10).iou(BoundingBox(5, 0, 15, 10)) == pytest.approx(1 / 3)


class TestDetectionScore:
    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_accepts_unit_interval(self, value: float) -> None:
        assert DetectionScore(value, ScoreType.GEOMETRIC_SIMILARITY).value == value

    @pytest.mark.parametrize("value", [-0.01, 1.01])
    def test_rejects_out_of_range(self, value: float) -> None:
        with pytest.raises(ValueError, match="within"):
            DetectionScore(value, ScoreType.MODEL_CONFIDENCE)


class TestImageSize:
    def test_rejects_non_positive_dimensions(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            ImageSize(width=0, height=10)

    def test_pixels(self) -> None:
        assert ImageSize(width=4, height=3).pixels == 12
