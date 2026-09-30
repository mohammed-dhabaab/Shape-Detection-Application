from collections.abc import Sequence

import numpy as np
import pytest

from app.application.dto import DecodedImage, EncodedImage, ImageFormat
from app.application.errors import EmptyFileError, UnsupportedImageFormatError
from app.application.use_cases import DetectShapes, in_reading_order
from app.domain.entities import Detection, ShapeType
from app.domain.value_objects import BoundingBox, DetectionScore, ScoreType
from app.infrastructure.image_processing import ImageLimits, PillowImageDecoder
from tests.fixtures.synthetic_images import encode, render


class StubDecoder:
    def __init__(self, width: int = 200, height: int = 100) -> None:
        self.image = DecodedImage(
            pixels=np.zeros((height, width, 3), dtype=np.uint8), source_format=ImageFormat.PNG
        )
        self.calls = 0

    def decode(self, data: bytes) -> DecodedImage:
        self.calls += 1
        return self.image


class FakeModelDetector:
    """Stands in for a future learned detector (e.g. YOLO) to prove the port is swappable."""

    def __init__(self, detections: list[Detection]) -> None:
        self.detections = detections
        self.received: DecodedImage | None = None

    def detect(self, image: DecodedImage) -> list[Detection]:
        self.received = image
        return list(self.detections)


class RecordingAnnotator:
    def __init__(self) -> None:
        self.detections: tuple[Detection, ...] = ()

    def annotate(self, image: DecodedImage, detections: Sequence[Detection]) -> EncodedImage:
        self.detections = tuple(detections)
        return EncodedImage(data=b"annotated", media_type="image/jpeg")


def model_detection(shape: ShapeType, x: int, y: int, confidence: float = 0.9) -> Detection:
    return Detection(
        shape=shape,
        bbox=BoundingBox(x, y, x + 20, y + 20),
        score=DetectionScore(confidence, ScoreType.MODEL_CONFIDENCE),
    )


def test_rejects_empty_upload_before_decoding() -> None:
    decoder = StubDecoder()
    use_case = DetectShapes(decoder, FakeModelDetector([]), RecordingAnnotator())

    with pytest.raises(EmptyFileError):
        use_case.execute(b"")
    assert decoder.calls == 0


def test_orchestrates_decode_detect_and_annotate() -> None:
    decoder = StubDecoder(width=200, height=100)
    detector = FakeModelDetector([model_detection(ShapeType.CIRCLE, 10, 10)])
    annotator = RecordingAnnotator()

    output = DetectShapes(decoder, detector, annotator).execute(b"image-bytes")

    assert detector.received is decoder.image
    assert output.result.image_size.width == 200
    assert output.result.image_size.height == 100
    assert output.annotated_image.data == b"annotated"
    assert annotator.detections == output.result.detections


def test_orders_detections_top_to_bottom_then_left_to_right() -> None:
    bottom = model_detection(ShapeType.SQUARE, 10, 70)
    top_right = model_detection(ShapeType.CIRCLE, 150, 5)
    top_left = model_detection(ShapeType.TRIANGLE, 20, 5)
    detector = FakeModelDetector([bottom, top_right, top_left])

    output = DetectShapes(StubDecoder(), detector, RecordingAnnotator()).execute(b"x")

    assert output.result.detections == (top_left, top_right, bottom)


def test_side_by_side_shapes_form_one_row_despite_uneven_tops() -> None:
    # The right-hand shape's top edge is slightly higher, but both sit on the same row.
    left = model_detection(ShapeType.CIRCLE, 10, 12)
    right = model_detection(ShapeType.PENTAGON, 100, 4)
    below = model_detection(ShapeType.SQUARE, 50, 60)

    assert in_reading_order([below, right, left]) == (left, right, below)


def test_preserves_score_semantics_of_the_detector() -> None:
    detector = FakeModelDetector(
        [
            model_detection(ShapeType.CIRCLE, 0, 0, 0.8),
            model_detection(ShapeType.CIRCLE, 50, 0, 1.0),
        ]
    )

    output = DetectShapes(StubDecoder(), detector, RecordingAnnotator()).execute(b"x")

    assert output.result.summary.score_type is ScoreType.MODEL_CONFIDENCE
    assert output.result.summary.average_score == pytest.approx(0.9)


def test_empty_detection_is_a_successful_result() -> None:
    output = DetectShapes(StubDecoder(), FakeModelDetector([]), RecordingAnnotator()).execute(b"x")

    assert output.result.detections == ()
    assert output.result.summary.total == 0


def test_propagates_decoder_validation_errors() -> None:
    decoder = PillowImageDecoder(ImageLimits(1000, 1000, 1_000_000))
    use_case = DetectShapes(decoder, FakeModelDetector([]), RecordingAnnotator())

    with pytest.raises(UnsupportedImageFormatError):
        use_case.execute(b"GIF89a not supported")


def test_works_with_real_decoder_and_swapped_detector() -> None:
    decoder = PillowImageDecoder(ImageLimits(1000, 1000, 1_000_000))
    detector = FakeModelDetector([model_detection(ShapeType.HEXAGON, 5, 5)])
    png = encode(render([], width=64, height=48))

    output = DetectShapes(decoder, detector, RecordingAnnotator()).execute(png)

    assert detector.received is not None
    assert detector.received.pixels.shape == (48, 64, 3)
    assert output.result.detections[0].shape is ShapeType.HEXAGON
