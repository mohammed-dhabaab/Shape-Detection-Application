from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(description="Stable machine-readable error code.", examples=["invalid_image"])
    message: str = Field(description="Human-readable explanation, safe to display.")
    details: list[dict[str, str]] | None = Field(
        default=None, description="Optional field-level details (validation errors)."
    )


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    error: ErrorDetail
    request_id: str | None = Field(
        default=None, description="Correlates the response with server logs."
    )


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    version: str
    detector: str
