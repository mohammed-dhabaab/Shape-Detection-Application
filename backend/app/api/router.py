from fastapi import APIRouter

from app.api.v1 import detection, health

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health.router)
v1_router.include_router(detection.router)

api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)
