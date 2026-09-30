from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

ALLOWED_ORIGIN = "http://localhost:3000"


def make_settings(**overrides: object) -> Settings:
    """Settings isolated from any local ``.env`` file."""
    defaults: dict[str, object] = {
        "environment": "test",
        "log_format": "console",
        "log_level": "WARNING",
        "allowed_origins": [ALLOWED_ORIGIN],
    }
    return Settings(_env_file=None, **{**defaults, **overrides})  # type: ignore[call-arg]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
