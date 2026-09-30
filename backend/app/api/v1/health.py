from fastapi import APIRouter

from app.api.dependencies import ServicesDep
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Service health check")
async def health(services: ServicesDep) -> HealthResponse:
    settings = services.settings
    return HealthResponse(
        status="ok", version=settings.app_version, detector=settings.detector_backend
    )
