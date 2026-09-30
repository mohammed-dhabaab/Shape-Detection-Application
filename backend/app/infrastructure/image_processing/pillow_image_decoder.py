"""Untrusted-input image decoding with Pillow.

Security posture: the filename, extension and client-declared MIME type are never
consulted. The format is identified from the file signature, dimensions are checked
from the header *before* pixel data is decompressed, and Pillow's decompression-bomb
warning is escalated to an error within a local ``warnings`` scope (no global state).
"""

import io
import warnings
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps, UnidentifiedImageError

from app.application.dto import DecodedImage, ImageFormat
from app.application.errors import (
    ImageDimensionsTooLargeError,
    InvalidImageError,
    UnsupportedImageFormatError,
)

_SIGNATURES: tuple[tuple[ImageFormat, bytes, int], ...] = (
    # (format, magic bytes, offset)
    (ImageFormat.JPEG, b"\xff\xd8\xff", 0),
    (ImageFormat.PNG, b"\x89PNG\r\n\x1a\n", 0),
    (ImageFormat.WEBP, b"WEBP", 8),  # "RIFF" <size:4> "WEBP"
)
_SUPPORTED_NAMES = tuple(fmt.value for fmt in ImageFormat)
_BACKGROUND_RGB = (255, 255, 255)
_ALPHA_MODES = frozenset({"RGBA", "LA", "PA", "RGBa", "La"})


@dataclass(frozen=True, slots=True)
class ImageLimits:
    max_width: int
    max_height: int
    max_pixels: int


class PillowImageDecoder:
    def __init__(self, limits: ImageLimits) -> None:
        self._limits = limits

    def decode(self, data: bytes) -> DecodedImage:
        image_format = sniff_image_format(data)
        if image_format is None:
            raise UnsupportedImageFormatError(_SUPPORTED_NAMES)

        formats = (image_format.value,)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            try:
                # Pass 1: header-only checks, then a structural integrity check.
                with Image.open(io.BytesIO(data), formats=formats) as probe:
                    self._check_dimensions(*probe.size)
                    probe.verify()
                # Pass 2: verify() leaves the image unusable, so reopen to decode pixels.
                with Image.open(io.BytesIO(data), formats=formats) as image:
                    image.load()
                    pixels = _to_bgr_array(image)
            except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
                raise ImageDimensionsTooLargeError(self._limits_message()) from exc
            except (UnidentifiedImageError, OSError, SyntaxError, ValueError, EOFError) as exc:
                raise InvalidImageError(
                    "The file appears to be corrupted or is not a valid image."
                ) from exc

        return DecodedImage(pixels=pixels, source_format=image_format)

    def _check_dimensions(self, width: int, height: int) -> None:
        limits = self._limits
        if (
            width > limits.max_width
            or height > limits.max_height
            or width * height > limits.max_pixels
        ):
            raise ImageDimensionsTooLargeError(
                f"Image dimensions {width}x{height} exceed the limit. {self._limits_message()}"
            )

    def _limits_message(self) -> str:
        limits = self._limits
        megapixels = limits.max_pixels / 1_000_000
        return (
            f"Maximum size is {limits.max_width}x{limits.max_height} "
            f"and {megapixels:.0f} megapixels."
        )


def sniff_image_format(data: bytes) -> ImageFormat | None:
    """Identify a supported format from its file signature, ignoring any metadata."""
    for image_format, magic, offset in _SIGNATURES:
        if data[offset : offset + len(magic)] == magic:
            if image_format is ImageFormat.WEBP and not data.startswith(b"RIFF"):
                continue
            return image_format
    return None


def _to_bgr_array(image: Image.Image) -> NDArray[np.uint8]:
    oriented = ImageOps.exif_transpose(image)
    has_alpha = oriented.mode in _ALPHA_MODES or (
        oriented.mode == "P" and "transparency" in oriented.info
    )
    if has_alpha:
        # Composite onto white: transparent pixels are otherwise black, which would
        # invent edges around every transparent region.
        rgba = oriented.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (*_BACKGROUND_RGB, 255))
        rgb = Image.alpha_composite(background, rgba).convert("RGB")
    else:
        rgb = oriented.convert("RGB")

    rgb_array = np.asarray(rgb, dtype=np.uint8)
    return np.ascontiguousarray(rgb_array[:, :, ::-1])
