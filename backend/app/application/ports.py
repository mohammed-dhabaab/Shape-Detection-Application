"""Interfaces the application layer depends on; infrastructure provides the adapters."""

from collections.abc import Sequence
from typing import Protocol

from app.application.dto import DecodedImage, EncodedImage
from app.domain.entities import Detection


class ImageDecoder(Protocol):
    def decode(self, data: bytes) -> DecodedImage:
        """Validate and decode raw bytes.

        Raises:
            UnsupportedImageFormatError, InvalidImageError, ImageDimensionsTooLargeError
        """
        ...


class ShapeDetector(Protocol):
    """Finds shapes in an image.

    Implementations must return bounding boxes in the coordinate space of ``image`` and
    choose the :class:`~app.domain.value_objects.ScoreType` that honestly describes
    their scores. The initial adapter is geometric (OpenCV); a trained model (e.g. YOLO)
    can replace it without touching the use case or the API.
    """

    def detect(self, image: DecodedImage) -> list[Detection]: ...


class ImageAnnotator(Protocol):
    def annotate(self, image: DecodedImage, detections: Sequence[Detection]) -> EncodedImage:
        """Render detections onto a copy of ``image`` and encode it for transport."""
        ...
