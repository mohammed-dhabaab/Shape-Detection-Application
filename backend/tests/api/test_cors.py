from fastapi.testclient import TestClient

from tests.conftest import ALLOWED_ORIGIN

PREFLIGHT_HEADERS = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


def test_preflight_from_allowed_origin_succeeds(client: TestClient) -> None:
    response = client.options(
        "/api/v1/detect", headers={"Origin": ALLOWED_ORIGIN, **PREFLIGHT_HEADERS}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "POST" in response.headers["access-control-allow-methods"]


def test_preflight_from_unknown_origin_is_rejected(client: TestClient) -> None:
    response = client.options(
        "/api/v1/detect", headers={"Origin": "https://evil.example", **PREFLIGHT_HEADERS}
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_simple_request_exposes_request_id_header(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]


def test_error_responses_carry_cors_headers(client: TestClient) -> None:
    response = client.post(
        "/api/v1/detect",
        files={"file": ("a.txt", b"hello", "text/plain")},
        headers={"Origin": ALLOWED_ORIGIN},
    )

    assert response.status_code == 415
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
