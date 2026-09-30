import cv2
import numpy as np

from app.application.dto import DecodedImage, ImageFormat
from app.domain.entities import Detection, ShapeType
from app.domain.value_objects import BoundingBox, DetectionScore, Outline, Point, ScoreType
from app.infrastructure.image_processing import AnnotationStyle, OpenCVImageAnnotator
from tests.fixtures.synthetic_images import render


def decode_jpeg(data: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    assert image is not None
    return image


def square_detection(box: tuple[int, int, int, int]) -> Detection:
    return Detection(
        shape=ShapeType.SQUARE,
        bbox=BoundingBox(*box),
        score=DetectionScore(0.93, ScoreType.GEOMETRIC_SIMILARITY),
    )


def test_encodes_jpeg_and_draws_boxes() -> None:
    image = DecodedImage(render([], width=400, height=300), ImageFormat.PNG)
    annotator = OpenCVImageAnnotator(AnnotationStyle())

    encoded = annotator.annotate(image, [square_detection((100, 100, 300, 250))])
    annotated = decode_jpeg(encoded.data)

    assert encoded.media_type == "image/jpeg"
    assert annotated.shape == (300, 400, 3)
    # The box edge is drawn in the square colour (red-ish in BGR), the centre untouched.
    blue, green, red = annotated[175, 100].astype(int)
    assert red > 150
    assert blue < 120
    assert green < 120
    assert tuple(annotated[175, 200]) >= (240, 240, 240)


def test_does_not_mutate_the_source_image() -> None:
    pixels = render([], width=200, height=200)
    original = pixels.copy()

    OpenCVImageAnnotator(AnnotationStyle()).annotate(
        DecodedImage(pixels, ImageFormat.PNG), [square_detection((10, 10, 150, 150))]
    )

    assert np.array_equal(pixels, original)


def test_downscales_large_images() -> None:
    image = DecodedImage(render([], width=3000, height=1500), ImageFormat.PNG)

    encoded = OpenCVImageAnnotator(AnnotationStyle(max_dimension=1000)).annotate(
        image, [square_detection((0, 0, 3000, 1500))]
    )

    assert decode_jpeg(encoded.data).shape == (500, 1000, 3)


def test_handles_no_detections() -> None:
    image = DecodedImage(render([], width=120, height=80), ImageFormat.PNG)

    encoded = OpenCVImageAnnotator(AnnotationStyle()).annotate(image, [])

    assert decode_jpeg(encoded.data).shape == (80, 120, 3)


def test_draws_the_outline_instead_of_the_box() -> None:
    image = DecodedImage(render([], width=400, height=300), ImageFormat.PNG)
    triangle = Detection(
        shape=ShapeType.TRIANGLE,
        bbox=BoundingBox(100, 60, 301, 261),
        score=DetectionScore(0.9, ScoreType.GEOMETRIC_SIMILARITY),
        outline=Outline((Point(200, 60), Point(300, 260), Point(100, 260))),
    )

    annotated = decode_jpeg(
        OpenCVImageAnnotator(AnnotationStyle()).annotate(image, [triangle]).data
    )

    # The triangle's edge is drawn in the triangle colour (green-ish, BGR) ...
    _, green, red = annotated[260, 200].astype(int)
    assert green > 120
    assert red < 120
    # ... while the bottom-left corner of its box, outside the triangle, stays blank.
    assert tuple(annotated[250, 110]) >= (235, 235, 235)
