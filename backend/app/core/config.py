from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_BYTES_PER_MB = 1024 * 1024


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and ``.env`` in development).

    Field names map to upper-case environment variables, e.g. ``max_file_size_mb`` ←
    ``MAX_FILE_SIZE_MB``.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Service -------------------------------------------------------------------------
    app_name: str = "Shape Detection API"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Comma-separated list of origins allowed by CORS.",
    )

    # --- Upload & resource limits --------------------------------------------------------
    max_file_size_mb: float = Field(default=10, gt=0)
    max_image_width: int = Field(default=7680, gt=0)
    max_image_height: int = Field(default=7680, gt=0)
    max_image_pixels: int = Field(default=40_000_000, gt=0)
    max_concurrent_detections: int = Field(default=2, gt=0)

    # --- Detection -----------------------------------------------------------------------
    detector_backend: Literal["opencv"] = "opencv"
    processing_max_dimension: int = Field(default=1600, ge=64)
    min_contour_area: float = Field(default=500, gt=0)
    contour_approximation_factor: float = Field(default=0.04, gt=0, lt=1)
    canny_low_threshold: int = Field(default=30, ge=0, le=255)
    canny_high_threshold: int = Field(default=100, ge=1, le=255)
    circle_min_circularity: float = Field(default=0.8, gt=0, le=1)
    circle_min_enclosing_fill: float = Field(default=0.88, gt=0, le=1)
    square_aspect_ratio_tolerance: float = Field(default=0.1, ge=0, lt=1)
    min_solidity: float = Field(default=0.9, gt=0, le=1)
    min_detection_score: float = Field(default=0.8, ge=0, le=1)
    duplicate_iou_threshold: float = Field(default=0.6, gt=0, le=1)

    # --- Annotation ----------------------------------------------------------------------
    annotated_image_max_dimension: int = Field(default=2048, ge=64)
    annotated_image_quality: int = Field(default=85, ge=1, le=100)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        if self.environment == "production" and "*" in self.allowed_origins:
            msg = "Wildcard CORS origins are not allowed in production"
            raise ValueError(msg)
        if self.canny_low_threshold >= self.canny_high_threshold:
            msg = "CANNY_LOW_THRESHOLD must be lower than CANNY_HIGH_THRESHOLD"
            raise ValueError(msg)
        return self

    @property
    def max_file_size_bytes(self) -> int:
        return int(self.max_file_size_mb * _BYTES_PER_MB)
