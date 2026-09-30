import cv2
import numpy as np
import pytest

from app.application.dto import DecodedImage, ImageFormat
from app.domain.entities import Detection, ShapeType
from app.domain.value_objects import BoundingBox, DetectionScore, ScoreType
from app.infrastructure.detectors.opencv import OpenCVDetectorConfig, OpenCVShapeDetector
from app.infrastructure.detectors.opencv.detector import merge_duplicates
from tests.fixtures.synthetic_images import (
    DARK,
    ShapeSpec,
    all_shapes_scene,
    encode,
    render,
)

BBOX_TOLERANCE_PX = 5

detector = OpenCVShapeDetector(OpenCVDetectorConfig())


def detect(pixels: np.ndarray) -> list[Detection]:
    return detector.detect(DecodedImage(pixels=pixels, source_format=ImageFormat.PNG))


def assert_bbox_close(actual: BoundingBox, expected: tuple[int, int, int, int]) -> None:
    coordinates = (actual.x1, actual.y1, actual.x2, actual.y2)
    assert all(
        abs(got - want) <= BBOX_TOLERANCE_PX
        for got, want in zip(coordinates, expected, strict=True)
    ), f"{coordinates} != {expected}"


def assert_matches(detections: list[Detection], shapes: list[ShapeSpec]) -> None:
    assert len(detections) == len(shapes), detections
    for spec in shapes:
        matches = [d for d in detections if d.shape.value == spec.name]
        assert matches, f"{spec.name} not detected in {detections}"
        best = max(matches, key=lambda d: d.bbox.iou(BoundingBox(*spec.expected_bbox())))
        assert_bbox_close(best.bbox, spec.expected_bbox())


@pytest.mark.parametrize(
    "spec",
    [
        ShapeSpec("circle", (300, 300), 120),
        ShapeSpec("triangle", (300, 300), 150),
        ShapeSpec("square", (300, 300), 220),
        ShapeSpec("rectangle", (300, 300), 300, aspect=0.5),
        ShapeSpec("pentagon", (300, 300), 150),
        ShapeSpec("hexagon", (300, 300), 150),
    ],
    ids=lambda spec: spec.name,
)
def test_detects_each_supported_shape(spec: ShapeSpec) -> None:
    detections = detect(render([spec]))

    assert_matches(detections, [spec])
    assert detections[0].score.type is ScoreType.GEOMETRIC_SIMILARITY
    assert detections[0].score.value >= 0.85


def test_detects_multiple_shapes_of_multiple_classes() -> None:
    shapes, pixels = all_shapes_scene()

    detections = detect(pixels)

    assert_matches(detections, shapes)
    assert {d.shape for d in detections} == set(ShapeType)


def test_detects_multiple_shapes_of_the_same_class() -> None:
    shapes = [ShapeSpec("circle", (150 + 250 * i, 300), 80) for i in range(3)]

    assert_matches(detect(render(shapes)), shapes)


@pytest.mark.parametrize("rotation", [15, 30, 45])
def test_rotated_square_is_still_a_square(rotation: float) -> None:
    spec = ShapeSpec("square", (300, 300), 200, rotation_deg=rotation)

    assert_matches(detect(render([spec])), [spec])


def test_detects_outlined_shapes_once() -> None:
    shapes = [
        ShapeSpec("circle", (150, 300), 90, thickness=5),
        ShapeSpec("triangle", (400, 300), 100, thickness=5),
        ShapeSpec("square", (650, 300), 180, thickness=5),
    ]

    assert_matches(detect(render(shapes)), shapes)


def test_detects_light_shapes_on_dark_background() -> None:
    spec = ShapeSpec("pentagon", (300, 300), 120, color=(235, 235, 235))

    assert_matches(detect(render([spec], background=DARK)), [spec])


def test_detects_shapes_that_differ_only_in_hue() -> None:
    # Pure green (BGR 0,128,0) on red (0,0,200) has similar luminance; per-channel edges
    # still separate them.
    spec = ShapeSpec("circle", (300, 300), 100, color=(0, 128, 0))

    assert_matches(detect(render([spec], background=(0, 0, 200))), [spec])


def test_detects_nested_shapes_of_different_classes() -> None:
    shapes = [
        ShapeSpec("square", (300, 300), 320, thickness=6),
        ShapeSpec("circle", (300, 300), 90, color=(0, 0, 220)),
    ]

    assert_matches(detect(render(shapes)), shapes)


def test_is_robust_to_noise_and_jpeg_compression() -> None:
    shapes, _ = all_shapes_scene()
    noisy = render(shapes, noise_sigma=12)
    jpeg = cv2.imdecode(np.frombuffer(encode(noisy, ".jpg"), np.uint8), cv2.IMREAD_COLOR)

    assert_matches(detect(jpeg), shapes)


def test_maps_boxes_back_to_original_scale_for_large_images() -> None:
    shapes, pixels = all_shapes_scene()  # 800x600
    factor = 5
    large = cv2.resize(pixels, None, fx=factor, fy=factor, interpolation=cv2.INTER_NEAREST)
    config = OpenCVDetectorConfig(processing_max_dimension=1000)

    detections = OpenCVShapeDetector(config).detect(DecodedImage(large, ImageFormat.PNG))

    assert len(detections) == len(shapes)
    for spec in shapes:
        x1, y1, x2, y2 = spec.expected_bbox()
        match = next(d for d in detections if d.shape.value == spec.name)
        scaled = BoundingBox(x1 * factor, y1 * factor, x2 * factor, y2 * factor)
        assert match.bbox.iou(scaled) > 0.9


@pytest.mark.parametrize(
    ("label", "pixels"),
    [
        ("blank", render([])),
        ("uniform dark", render([], background=DARK)),
        (
            "horizontal gradient",
            np.repeat(np.tile(np.linspace(0, 255, 800, dtype=np.uint8), (600, 1))[..., None], 3, 2),
        ),
        ("shape below minimum area", render([ShapeSpec("circle", (300, 300), 10)])),
    ],
)
def test_returns_nothing_when_no_supported_shape_is_present(label: str, pixels: np.ndarray) -> None:
    assert detect(np.ascontiguousarray(pixels)) == [], label


def test_ignores_unsupported_shapes() -> None:
    canvas = render([])
    cv2.ellipse(canvas, (250, 300), (200, 70), 0, 0, 360, (0, 0, 200), -1)
    angles = np.linspace(-np.pi / 2, 3 * np.pi / 2, 10, endpoint=False)
    radii = np.where(np.arange(10) % 2 == 0, 120, 50)
    star = np.stack([600 + radii * np.cos(angles), 300 + radii * np.sin(angles)], axis=1)
    cv2.fillPoly(canvas, [star.astype(np.int32)], (40, 90, 200))

    assert detect(canvas) == []


def test_minimum_contour_area_is_configurable() -> None:
    spec = ShapeSpec("circle", (300, 300), 20)  # area ~1250 px²
    strict = OpenCVShapeDetector(OpenCVDetectorConfig(min_contour_area=5000))

    assert detect(render([spec]))
    assert strict.detect(DecodedImage(render([spec]), ImageFormat.PNG)) == []


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="odd"):
        OpenCVDetectorConfig(blur_kernel_size=4)
    with pytest.raises(ValueError, match="canny"):
        OpenCVDetectorConfig(canny_low_threshold=100, canny_high_threshold=50)


class TestMergeDuplicates:
    @staticmethod
    def make(shape: ShapeType, box: tuple[int, int, int, int], score: float) -> Detection:
        return Detection(
            shape=shape,
            bbox=BoundingBox(*box),
            score=DetectionScore(score, ScoreType.GEOMETRIC_SIMILARITY),
        )

    def test_keeps_best_score_and_outermost_extent(self) -> None:
        outer = self.make(ShapeType.SQUARE, (0, 0, 100, 100), 0.85)
        inner = self.make(ShapeType.SQUARE, (4, 4, 96, 96), 0.95)

        (merged,) = merge_duplicates([outer, inner], 0.6)

        assert merged.score.value == 0.95
        assert merged.bbox == BoundingBox(0, 0, 100, 100)

    def test_keeps_overlapping_detections_of_different_classes(self) -> None:
        square = self.make(ShapeType.SQUARE, (0, 0, 100, 100), 0.9)
        circle = self.make(ShapeType.CIRCLE, (1, 1, 99, 99), 0.9)

        assert len(merge_duplicates([square, circle], 0.6)) == 2

    def test_keeps_distant_detections_of_the_same_class(self) -> None:
        first = self.make(ShapeType.CIRCLE, (0, 0, 50, 50), 0.9)
        second = self.make(ShapeType.CIRCLE, (200, 200, 250, 250), 0.9)

        assert len(merge_duplicates([first, second], 0.6)) == 2
