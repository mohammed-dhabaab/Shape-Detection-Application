from typing import Annotated, Any

import anyio
from fastapi import APIRouter, File, UploadFile

from app.api.dependencies import ServicesDep
from app.api.upload import read_upload_limited
from app.schemas.common import ErrorResponse
from app.schemas.detection import DetectionResponse

router = APIRouter(tags=["detection"])

_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Empty, corrupted or undecodable image."},
    413: {"model": ErrorResponse, "description": "File exceeds the upload size limit."},
    415: {"model": ErrorResponse, "description": "File is not a JPEG, PNG or WebP image."},
    422: {"model": ErrorResponse, "description": "Missing file or image dimensions too large."},
    500: {"model": ErrorResponse, "description": "Unexpected server error."},
}


@router.post(
    "/detect",
    summary="Detect geometric shapes in an image",
    description=(
        "Accepts a JPEG, PNG or WebP image as multipart form data (`file` field) and "
        "returns detected shapes, bounding boxes, scores, summary statistics and an "
        "annotated image. An image without shapes is a successful, empty result."
    ),
    responses=_ERROR_RESPONSES,
)
async def detect_shapes(
    file: Annotated[UploadFile, File(description="Image to analyse (JPEG, PNG or WebP).")],
    services: ServicesDep,
) -> DetectionResponse:
    data = await read_upload_limited(file, services.settings.max_file_size_bytes)
    # Image processing is CPU-bound: run it off the event loop, with bounded concurrency.
    output = await anyio.to_thread.run_sync(
        services.detect_shapes.execute, data, limiter=services.detection_limiter
    )
    return DetectionResponse.from_output(output)
