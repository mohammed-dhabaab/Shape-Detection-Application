from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from app.domain.value_objects import ImageSize


class ImageFormat(StrEnum):
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"


@dataclass(frozen=True, slots=True)
class DecodedImage:
    """A validated image ready for analysis.

    Pixels are an ``(height, width, 3)`` ``uint8`` array in **BGR** channel order. numpy
    is used as the neutral pixel container because every realistic detector backend
    (OpenCV, ONNX Runtime, Ultralytics YOLO, ...) consumes it directly.
    """

    pixels: NDArray[np.uint8]
    source_format: ImageFormat

    def __post_init__(self) -> None:
        if self.pixels.ndim != 3 or self.pixels.shape[2] != 3:
            msg = f"Expected an (H, W, 3) array, got shape {self.pixels.shape}"
            raise ValueError(msg)

    @property
    def size(self) -> ImageSize:
        height, width = self.pixels.shape[:2]
        return ImageSize(width=int(width), height=int(height))


@dataclass(frozen=True, slots=True)
class EncodedImage:
    data: bytes
    media_type: str
