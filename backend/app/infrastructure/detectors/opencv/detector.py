"""Classical computer-vision shape detector.

Pipeline: downscale → blur → per-channel Canny → morphological close → contours →
area filter → measure → classify (domain rules) → map boxes to original scale →
merge duplicates.

Scores are *geometric similarity* (how closely a contour matches the ideal shape),
never a learned confidence, and are labelled as such.
"""

import math
from collections.abc import Iterable
from dataclasses import replace

import cv2
import numpy as np
from cv2.typing import MatLike

from app.application.dto import DecodedImage
from app.domain.entities import Detection
from app.domain.services import ShapeClassifier
from app.domain.value_objects import BoundingBox, DetectionScore, ImageSize, ScoreType
from app.infrastructure.detectors.opencv.config import OpenCVDetectorConfig
from app.infrastructure.detectors.opencv.features import measure_contour


class OpenCVShapeDetector:
    def __init__(self, config: OpenCVDetectorConfig) -> None:
        self._config = config
        self._classifier = ShapeClassifier(config.classification)
        self._morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (config.morph_kernel_size, config.morph_kernel_size)
        )

    def detect(self, image: DecodedImage) -> list[Detection]:
        original_size = image.size
        scale = min(
            1.0,
            self._config.processing_max_dimension / max(original_size.width, original_size.height),
        )
        pixels = self._resize(image.pixels, scale)
        working_area = pixels.shape[0] * pixels.shape[1]

        min_area = self._config.min_contour_area * scale**2
        max_area = self._config.max_contour_area_ratio * working_area

        contours, _ = cv2.findContours(
            self._edge_map(pixels), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        candidates: list[Detection] = []
        for contour in contours:
            if not min_area <= cv2.contourArea(contour) <= max_area:
                continue
            detection = self._classify(contour, scale, original_size)
            if detection is not None:
                candidates.append(detection)

        return merge_duplicates(candidates, self._config.duplicate_iou_threshold)

    def _edge_map(self, pixels: MatLike) -> MatLike:
        kernel = (self._config.blur_kernel_size, self._config.blur_kernel_size)
        blurred = cv2.GaussianBlur(pixels, kernel, 0)
        # Canny per colour channel rather than on grayscale alone, so shapes whose
        # colour differs from the background but whose luminance does not (e.g. red on
        # green) still produce edges.
        edges = np.zeros(blurred.shape[:2], dtype=np.uint8)
        for channel in cv2.split(blurred):
            channel_edges = cv2.Canny(
                channel, self._config.canny_low_threshold, self._config.canny_high_threshold
            )
            edges = cv2.bitwise_or(edges, channel_edges)
        return cv2.morphologyEx(edges, cv2.MORPH_CLOSE, self._morph_kernel)

    def _classify(
        self, contour: MatLike, scale: float, original_size: ImageSize
    ) -> Detection | None:
        features = measure_contour(contour, self._config.approximation_factor)
        if features is None:
            return None
        classification = self._classifier.classify(features)
        if classification is None:
            return None
        return Detection(
            shape=classification.shape,
            bbox=_to_original_bbox(_bounding_rect(contour), scale, original_size),
            score=DetectionScore(
                value=round(classification.similarity, 4),
                type=ScoreType.GEOMETRIC_SIMILARITY,
            ),
        )

    @staticmethod
    def _resize(pixels: MatLike, scale: float) -> MatLike:
        if scale >= 1.0:
            return pixels
        height, width = pixels.shape[:2]
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        return cv2.resize(pixels, size, interpolation=cv2.INTER_AREA)


def merge_duplicates(detections: Iterable[Detection], iou_threshold: float) -> list[Detection]:
    """Class-aware non-maximum suppression that merges duplicate contours of one shape.

    A shape's edges yield several near-concentric contours (both sides of the edge; for
    outlined shapes, both sides of the stroke). The merged detection keeps the best
    score and the outermost extent, which is the shape's visible boundary.

    Class-aware so that genuinely nested shapes of different classes (a circle inside a
    square) survive even when their boxes overlap heavily.
    """
    kept: list[Detection] = []
    for candidate in sorted(detections, key=lambda d: d.score.value, reverse=True):
        for index, existing in enumerate(kept):
            if existing.shape == candidate.shape and existing.bbox.iou(candidate.bbox) >= (
                iou_threshold
            ):
                kept[index] = replace(existing, bbox=existing.bbox.enclosing(candidate.bbox))
                break
        else:
            kept.append(candidate)
    return kept


def _bounding_rect(contour: MatLike) -> tuple[int, int, int, int]:
    x, y, width, height = cv2.boundingRect(contour)
    return int(x), int(y), int(width), int(height)


def _to_original_bbox(
    rect: tuple[int, int, int, int], scale: float, original_size: ImageSize
) -> BoundingBox:
    x, y, width, height = rect
    x1 = min(math.floor(x / scale), original_size.width - 1)
    y1 = min(math.floor(y / scale), original_size.height - 1)
    x2 = max(min(math.ceil((x + width) / scale), original_size.width), x1 + 1)
    y2 = max(min(math.ceil((y + height) / scale), original_size.height), y1 + 1)
    return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)
