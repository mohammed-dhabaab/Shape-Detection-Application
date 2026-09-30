"""Composition root: the only place that knows which adapters implement which ports."""

from dataclasses import dataclass
from typing import Annotated, cast

from anyio import CapacityLimiter
from fastapi import Depends, Request

from app.application.ports import ShapeDetector
from app.application.use_cases import DetectShapes
from app.core.config import Settings
from app.domain.services import ClassificationRules
from app.infrastructure.detectors.opencv import OpenCVDetectorConfig, OpenCVShapeDetector
from app.infrastructure.image_processing import (
    AnnotationStyle,
    ImageLimits,
    OpenCVImageAnnotator,
    PillowImageDecoder,
)


@dataclass(frozen=True, slots=True)
class Services:
    settings: Settings
    detect_shapes: DetectShapes
    detection_limiter: CapacityLimiter


def build_services(settings: Settings) -> Services:
    return Services(
        settings=settings,
        detect_shapes=build_detect_shapes(settings),
        # Detection is CPU- and memory-heavy; bound how many run at once.
        detection_limiter=CapacityLimiter(settings.max_concurrent_detections),
    )


def build_detect_shapes(settings: Settings) -> DetectShapes:
    return DetectShapes(
        decoder=PillowImageDecoder(
            ImageLimits(
                max_width=settings.max_image_width,
                max_height=settings.max_image_height,
                max_pixels=settings.max_image_pixels,
            )
        ),
        detector=build_detector(settings),
        annotator=OpenCVImageAnnotator(
            AnnotationStyle(
                max_dimension=settings.annotated_image_max_dimension,
                jpeg_quality=settings.annotated_image_quality,
            )
        ),
    )


def build_detector(settings: Settings) -> ShapeDetector:
    """Select the detector implementation. A YOLO adapter would be one more case here."""
    match settings.detector_backend:
        case "opencv":
            return OpenCVShapeDetector(
                OpenCVDetectorConfig(
                    min_contour_area=settings.min_contour_area,
                    approximation_factor=settings.contour_approximation_factor,
                    processing_max_dimension=settings.processing_max_dimension,
                    canny_low_threshold=settings.canny_low_threshold,
                    canny_high_threshold=settings.canny_high_threshold,
                    duplicate_iou_threshold=settings.duplicate_iou_threshold,
                    classification=ClassificationRules(
                        min_solidity=settings.min_solidity,
                        circle_min_circularity=settings.circle_min_circularity,
                        circle_min_enclosing_fill=settings.circle_min_enclosing_fill,
                        square_aspect_ratio_tolerance=settings.square_aspect_ratio_tolerance,
                        min_score=settings.min_detection_score,
                    ),
                )
            )


def get_services(request: Request) -> Services:
    return cast(Services, request.app.state.services)


ServicesDep = Annotated[Services, Depends(get_services)]
