import io
import struct
import zlib

import numpy as np
import pytest
from PIL import Image

from app.application.dto import ImageFormat
from app.application.errors import (
    ImageDimensionsTooLargeError,
    InvalidImageError,
    UnsupportedImageFormatError,
)
from app.infrastructure.image_processing import ImageLimits, PillowImageDecoder
from app.infrastructure.image_processing.pillow_image_decoder import sniff_image_format

decoder = PillowImageDecoder(ImageLimits(max_width=4000, max_height=4000, max_pixels=10_000_000))


def pillow_bytes(image: Image.Image, image_format: str, **params: object) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **params)
    return buffer.getvalue()


def red_image(width: int = 40, height: int = 30) -> Image.Image:
    return Image.new("RGB", (width, height), (255, 0, 0))


@pytest.mark.parametrize(
    ("image_format", "expected"),
    [("JPEG", ImageFormat.JPEG), ("PNG", ImageFormat.PNG), ("WEBP", ImageFormat.WEBP)],
)
def test_decodes_supported_formats_to_bgr(image_format: str, expected: ImageFormat) -> None:
    decoded = decoder.decode(pillow_bytes(red_image(), image_format))

    assert decoded.source_format is expected
    assert decoded.pixels.shape == (30, 40, 3)
    assert decoded.pixels.dtype == np.uint8
    blue, green, red = decoded.pixels[15, 20]  # BGR channel order
    assert red > 200
    assert green < 60
    assert blue < 60


@pytest.mark.parametrize("image_format", ["GIF", "BMP", "TIFF"])
def test_rejects_valid_images_in_unsupported_formats(image_format: str) -> None:
    with pytest.raises(UnsupportedImageFormatError) as exc_info:
        decoder.decode(pillow_bytes(red_image(), image_format))

    assert exc_info.value.code == "unsupported_format"


def test_rejects_non_image_content_regardless_of_name() -> None:
    with pytest.raises(UnsupportedImageFormatError):
        decoder.decode(b"%PDF-1.7 definitely not an image")


def test_rejects_truncated_jpeg() -> None:
    data = pillow_bytes(red_image(400, 300), "JPEG")

    with pytest.raises(InvalidImageError):
        decoder.decode(data[: len(data) // 2])


def test_rejects_png_signature_followed_by_garbage() -> None:
    with pytest.raises(InvalidImageError):
        decoder.decode(b"\x89PNG\r\n\x1a\n" + b"\x00garbage" * 20)


def test_rejects_png_with_corrupted_pixel_data() -> None:
    data = bytearray(pillow_bytes(red_image(), "PNG"))
    idat = data.index(b"IDAT")
    data[idat + 8 : idat + 16] = b"\xff" * 8  # corrupt compressed data, CRC now wrong

    with pytest.raises(InvalidImageError):
        decoder.decode(bytes(data))


def test_composites_transparency_onto_white() -> None:
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    image.paste((0, 0, 255, 255), (5, 5, 15, 15))

    decoded = decoder.decode(pillow_bytes(image, "PNG"))

    assert tuple(decoded.pixels[0, 0]) == (255, 255, 255)  # transparent → white
    assert tuple(decoded.pixels[10, 10]) == (255, 0, 0)  # opaque blue (BGR)


def test_applies_exif_orientation() -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90° clockwise on display
    data = pillow_bytes(red_image(200, 100), "JPEG", exif=exif)

    decoded = decoder.decode(data)

    assert decoded.size.width == 100
    assert decoded.size.height == 200


@pytest.mark.parametrize(
    ("width", "height", "limits"),
    [
        (300, 50, ImageLimits(max_width=200, max_height=200, max_pixels=1_000_000)),
        (50, 300, ImageLimits(max_width=200, max_height=200, max_pixels=1_000_000)),
        (150, 150, ImageLimits(max_width=200, max_height=200, max_pixels=10_000)),
    ],
)
def test_rejects_images_exceeding_dimension_limits(
    width: int, height: int, limits: ImageLimits
) -> None:
    with pytest.raises(ImageDimensionsTooLargeError):
        PillowImageDecoder(limits).decode(pillow_bytes(red_image(width, height), "PNG"))


def _png_with_declared_size(width: int, height: int) -> bytes:
    """A tiny PNG whose header claims enormous dimensions (a decompression bomb)."""
    data = bytearray(pillow_bytes(Image.new("L", (1, 1)), "PNG"))
    ihdr = data.index(b"IHDR")
    data[ihdr + 4 : ihdr + 12] = struct.pack(">II", width, height)
    crc = zlib.crc32(bytes(data[ihdr : ihdr + 17]))
    data[ihdr + 17 : ihdr + 21] = struct.pack(">I", crc)
    return bytes(data)


def test_rejects_decompression_bombs_before_decoding() -> None:
    permissive = PillowImageDecoder(
        ImageLimits(max_width=200_000, max_height=200_000, max_pixels=10**11)
    )

    with pytest.raises(ImageDimensionsTooLargeError):
        permissive.decode(_png_with_declared_size(100_000, 100_000))


def test_sniffing_ignores_riff_files_that_are_not_webp() -> None:
    assert sniff_image_format(b"RIFF\x00\x00\x00\x00WAVEfmt ") is None
    assert sniff_image_format(b"RIFF\x00\x00\x00\x00WEBPVP8 ") is ImageFormat.WEBP
