"""Translate exceptions into consistent ``ErrorResponse`` bodies.

Expected failures (application errors, validation, HTTP errors) are logged at
warning level with their message. Unexpected ones are handled in
``RequestContextMiddleware``: logged with a stack trace and answered with a generic
message so internals never leak to clients.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.errors import (
    EmptyFileError,
    FileTooLargeError,
    ImageDimensionsTooLargeError,
    InvalidImageError,
    ShapeDetectionError,
    UnsupportedImageFormatError,
)
from app.core.logging import request_id_var
from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

_STATUS_BY_ERROR: dict[type[ShapeDetectionError], HTTPStatus] = {
    EmptyFileError: HTTPStatus.BAD_REQUEST,
    InvalidImageError: HTTPStatus.BAD_REQUEST,
    FileTooLargeError: HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    UnsupportedImageFormatError: HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
    ImageDimensionsTooLargeError: HTTPStatus.UNPROCESSABLE_ENTITY,
}


def error_response(
    status: HTTPStatus,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    request_id = request_id_var.get()
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details),
        request_id=request_id,
    )
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(
        status_code=status, content=body.model_dump(exclude_none=True), headers=headers
    )


def status_for(error: ShapeDetectionError) -> HTTPStatus:
    for error_type in type(error).__mro__:
        if error_type in _STATUS_BY_ERROR:
            return _STATUS_BY_ERROR[error_type]
    return HTTPStatus.BAD_REQUEST


def internal_error_response() -> JSONResponse:
    return error_response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "internal_error",
        "An unexpected error occurred while processing the request. Please try again.",
    )


def register_error_handlers(app: FastAPI) -> None:
    # Unexpected exceptions are handled by RequestContextMiddleware, which still has the
    # request ID in scope and sits inside CORS (Starlette's own 500 handler has neither).

    @app.exception_handler(ShapeDetectionError)
    async def handle_application_error(_: Request, exc: ShapeDetectionError) -> JSONResponse:
        status = status_for(exc)
        logger.warning(
            "Request rejected: %s", exc.code, extra={"error_code": exc.code, "status": int(status)}
        )
        return error_response(status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", ()) if part != "body"),
                "message": str(error.get("msg", "Invalid value")),
            }
            for error in exc.errors()
        ]
        return error_response(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "validation_error",
            "The request is invalid. Send the image as multipart form data in the 'file' field.",
            details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        status = HTTPStatus(exc.status_code)
        code = status.phrase.lower().replace(" ", "_").replace("-", "_")
        message = exc.detail if isinstance(exc.detail, str) else status.phrase
        return error_response(status, code, message)
