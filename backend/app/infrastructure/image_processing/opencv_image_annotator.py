"""Renders detections onto an image for human review."""

from collections.abc import Sequence
from dataclasses import dataclass

import cv2
from cv2.typing import MatLike

from app.application.dto import DecodedImage, EncodedImage
from app.domain.entities import Detection, ShapeType

# BGR. Mirrors the frontend's shape palette (frontend/src/entities/detection/lib/shape-meta.ts)
# so the annotated image and the results list share a visual language.
_SHAPE_COLORS: dict[ShapeType, tuple[int, int, int]] = {
    ShapeType.CIRCLE: (235, 99, 37),  # #2563eb
    ShapeType.TRIANGLE: (74, 163, 22),  # #16a34a
    ShapeType.SQUARE: (38, 38, 220),  # #dc2626
    ShapeType.RECTANGLE: (6, 119, 217),  # #d97706
    ShapeType.PENTAGON: (234, 51, 147),  # #9333ea
    ShapeType.HEXAGON: (178, 145, 8),  # #0891b2
}
_LABEL_TEXT_COLOR = (255, 255, 255)
_FONT = cv2.FONT_HERSHEY_SIMPLEX
# Stroke and label sizes are proportional to the rendered image so annotations stay
# legible on both thumbnails and large images.
_STROKE_DIVISOR = 350
_FONT_DIVISOR = 1100
_MIN_FONT_SCALE = 0.45


@dataclass(frozen=True, slots=True)
class AnnotationStyle:
    max_dimension: int = 2048
    jpeg_quality: int = 85


class OpenCVImageAnnotator:
    def __init__(self, style: AnnotationStyle) -> None:
        self._style = style

    def annotate(self, image: DecodedImage, detections: Sequence[Detection]) -> EncodedImage:
        size = image.size
        scale = min(1.0, self._style.max_dimension / max(size.width, size.height))
        canvas = _resized_copy(image.pixels, scale)

        short_side = min(canvas.shape[:2])
        stroke = max(2, round(short_side / _STROKE_DIVISOR))
        font_scale = max(_MIN_FONT_SCALE, short_side / _FONT_DIVISOR)

        # Numbered in the same order as the API response so "#2" in the image is
        # detection id 2 in the list.
        for number, detection in enumerate(detections, start=1):
            _draw_detection(
                canvas,
                detection,
                number=number,
                scale=scale,
                stroke=stroke,
                font_scale=font_scale,
            )

        ok, buffer = cv2.imencode(
            ".jpg", canvas, [cv2.IMWRITE_JPEG_QUALITY, self._style.jpeg_quality]
        )
        if not ok:  # pragma: no cover - only fails on OpenCV build misconfiguration
            msg = "Failed to encode annotated image"
            raise RuntimeError(msg)
        return EncodedImage(data=buffer.tobytes(), media_type="image/jpeg")


def _resized_copy(pixels: MatLike, scale: float) -> MatLike:
    if scale >= 1.0:
        return pixels.copy()
    height, width = pixels.shape[:2]
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(pixels, size, interpolation=cv2.INTER_AREA)


def _draw_detection(
    canvas: MatLike,
    detection: Detection,
    *,
    number: int,
    scale: float,
    stroke: int,
    font_scale: float,
) -> None:
    color = _SHAPE_COLORS[detection.shape]
    bbox = detection.bbox
    top_left = (round(bbox.x1 * scale), round(bbox.y1 * scale))
    bottom_right = (round(bbox.x2 * scale) - 1, round(bbox.y2 * scale) - 1)
    cv2.rectangle(canvas, top_left, bottom_right, color, stroke, cv2.LINE_AA)

    label = f"#{number} {detection.shape.value} {detection.score.value:.0%}"
    text_thickness = max(1, stroke // 2)
    (text_width, text_height), baseline = cv2.getTextSize(label, _FONT, font_scale, text_thickness)
    padding = stroke + 2
    label_height = text_height + baseline + padding
    # Place the label above the box when there is room, otherwise inside its top edge.
    label_top = top_left[1] - label_height if top_left[1] >= label_height else top_left[1]
    label_right = min(top_left[0] + text_width + 2 * padding, canvas.shape[1] - 1)
    cv2.rectangle(
        canvas, (top_left[0], label_top), (label_right, label_top + label_height), color, -1
    )
    cv2.putText(
        canvas,
        label,
        (top_left[0] + padding, label_top + text_height + padding // 2),
        _FONT,
        font_scale,
        _LABEL_TEXT_COLOR,
        text_thickness,
        cv2.LINE_AA,
    )
