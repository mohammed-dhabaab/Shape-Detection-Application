from fastapi.testclient import TestClient


def test_health_reports_status_version_and_detector(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0", "detector": "opencv"}


def test_every_response_carries_a_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert len(response.headers["X-Request-ID"]) == 32


def test_valid_incoming_request_id_is_propagated(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "trace-123"})

    assert response.headers["X-Request-ID"] == "trace-123"


def test_unsafe_incoming_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "bad id\twith spaces"})

    assert response.headers["X-Request-ID"] != "bad id\twith spaces"


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
