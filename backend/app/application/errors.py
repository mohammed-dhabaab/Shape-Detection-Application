"""Expected, user-facing failures of the detection workflow.

These errors are framework-agnostic; the API layer maps them to HTTP responses.
Each error carries a stable machine-readable ``code`` that clients can switch on.
"""

from typing import ClassVar


class ShapeDetectionError(Exception):
    code: ClassVar[str] = "detection_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmptyFileError(ShapeDetectionError):
    code = "empty_file"

    def __init__(self) -> None:
        super().__init__("The uploaded file is empty.")


class FileTooLargeError(ShapeDetectionError):
    code = "file_too_large"

    def __init__(self, max_bytes: int) -> None:
        super().__init__(f"The uploaded file exceeds the {max_bytes // (1024 * 1024)} MB limit.")
        self.max_bytes = max_bytes


class UnsupportedImageFormatError(ShapeDetectionError):
    code = "unsupported_format"

    def __init__(self, supported: tuple[str, ...]) -> None:
        super().__init__(f"Unsupported file type. Supported formats: {', '.join(supported)}.")
        self.supported = supported


class InvalidImageError(ShapeDetectionError):
    code = "invalid_image"

    def __init__(self, reason: str = "The file could not be decoded as an image.") -> None:
        super().__init__(reason)


class ImageDimensionsTooLargeError(ShapeDetectionError):
    code = "image_too_large"
