"""Application factory.

Run with ``uvicorn app.main:create_app --factory``. A factory (rather than a module-level
``app``) keeps imports free of side effects and lets tests build apps with custom
settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import build_services
from app.api.error_handlers import REQUEST_ID_HEADER, register_error_handlers
from app.api.middleware import BodySizeLimitMiddleware, RequestContextMiddleware
from app.api.router import api_router
from app.core.config import Settings
from app.core.logging import configure_logging

# Allowance for multipart boundaries and part headers on top of the file itself.
_MULTIPART_OVERHEAD_BYTES = 64 * 1024


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        summary="Detects and classifies geometric shapes in uploaded images.",
    )
    app.state.services = build_services(settings)
    register_error_handlers(app)

    # Starlette runs the last-added middleware first. Order (outermost → innermost):
    # CORS → request context → body size limit, so every response the browser sees,
    # including 413s and 500s, carries CORS headers and a request ID.
    app.add_middleware(
        BodySizeLimitMiddleware,
        max_body_bytes=settings.max_file_size_bytes + _MULTIPART_OVERHEAD_BYTES,
        max_file_bytes=settings.max_file_size_bytes,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
        max_age=600,
    )

    app.include_router(api_router)
    return app
