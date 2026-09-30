"""Classical computer-vision shape detector.

Pipeline: downscale → blur → per-channel Canny → morphological close → contours (plus
outlines recovered by merging faces split by crossing lines, see ``regions``) → area
filter → measure → classify (domain rules) → map boxes to original scale → merge
duplicates.

Scores are *geometric similarity* (how closely a contour matches the ideal shape),
never a learned confidence, and are labelled as such.
"""

import math
from collections.abc import Iterable
from dataclasses import replace
from itertools import chain

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray

from app.application.dto import DecodedImage
from app.domain.entities import Detection
from app.domain.services import Classification, ShapeClassifier
from app.domain.value_objects import (
    BoundingBox,
    DetectionScore,
    ImageSize,
    Outline,
    Point,
    ScoreType,
)
from app.infrastructure.detectors.opencv.config import OpenCVDetectorConfig
from app.infrastructure.detectors.opencv.features import measure_contour
from app.infrastructure.detectors.opencv.outline import trace_outline
from app.infrastructure.detectors.opencv.regions import merged_region_contours


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

        edges = self._edge_map(pixels)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        merged_outlines = merged_region_contours(
            edges,
            min_area=min_area,
            config=self._config.region_merge,
            is_shape=lambda outline: self._classification(outline) is not None,
        )

        candidates: list[Detection] = []
        for outline in chain(contours, merged_outlines):
            if not min_area <= cv2.contourArea(outline) <= max_area:
                continue
            detection = self._detection(outline, scale, original_size)
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

    def _classification(self, contour: MatLike) -> Classification | None:
        features = measure_contour(contour, self._config.approximation_factor)
        return None if features is None else self._classifier.classify(features)

    def _detection(
        self, contour: MatLike, scale: float, original_size: ImageSize
    ) -> Detection | None:
        classification = self._classification(contour)
        if classification is None:
            return None
        # Tolerance is given in original-image pixels; the contour is at processing scale.
        points = trace_outline(contour, self._config.outline_tolerance * scale)
        outline = _to_original_outline(points, scale, original_size) if points is not None else None
        return Detection(
            shape=classification.shape,
            bbox=_to_original_bbox(_bounding_rect(contour), scale, original_size),
            score=DetectionScore(
                value=round(classification.similarity, 4),
                type=ScoreType.GEOMETRIC_SIMILARITY,
            ),
            outline=outline,
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
    score and the geometry (outline and box) of the outermost candidate, which is the
    shape's visible boundary.

    Class-aware so that genuinely nested shapes of different classes (a circle inside a
    square) survive even when their boxes overlap heavily.
    """
    kept: list[Detection] = []
    for candidate in sorted(detections, key=lambda d: d.score.value, reverse=True):
        for index, existing in enumerate(kept):
            if existing.shape == candidate.shape and existing.bbox.iou(candidate.bbox) >= (
                iou_threshold
            ):
                outline = (
                    candidate.outline
                    if candidate.bbox.area > existing.bbox.area
                    else existing.outline
                )
                kept[index] = replace(
                    existing, bbox=existing.bbox.enclosing(candidate.bbox), outline=outline
                )
                break
        else:
            kept.append(candidate)
    return kept


def _to_original_outline(
    points: NDArray[np.float64], scale: float, original_size: ImageSize
) -> Outline | None:
    scaled = np.rint(points / scale).astype(np.int64)
    xs = np.clip(scaled[:, 0], 0, original_size.width - 1)
    ys = np.clip(scaled[:, 1], 0, original_size.height - 1)
    unique: list[Point] = []
    for x, y in zip(xs.tolist(), ys.tolist(), strict=True):
        point = Point(x=x, y=y)
        if not unique or unique[-1] != point:
            unique.append(point)
    if len(unique) > 1 and unique[0] == unique[-1]:
        unique.pop()
    return Outline(tuple(unique)) if len(unique) >= 3 else None


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
