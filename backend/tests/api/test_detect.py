import base64
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import Services, get_services
from app.core.config import Settings
from app.main import create_app
from tests.conftest import make_settings
from tests.fixtures.synthetic_images import ShapeSpec, all_shapes_scene, encode, render

DETECT_URL = "/api/v1/detect"


class TestSuccessfulDetection:
    def test_single_shape(self, client: TestClient) -> None:
        png = encode(render([ShapeSpec("circle", (300, 300), 120)]))

        response = client.post(DETECT_URL, files={"file": ("circle.png", png, "image/png")})

        assert response.status_code == 200
        body = response.json()
        assert body["image"] == {"width": 800, "height": 600}
        assert len(body["detections"]) == 1
        detection = body["detections"][0]
        assert detection["id"] == 1
        assert detection["class_name"] == "circle"
        assert detection["score_type"] == "geometric_similarity"
        assert 0.85 <= detection["score"] <= 1
        assert set(detection["bbox"]) == {"x1", "y1", "x2", "y2"}
        outline = detection["outline"]
        assert len(outline) >= 8
        assert all(
            len(point) == 2 and 0 <= point[0] < 800 and 0 <= point[1] < 600 for point in outline
        )
        assert body["summary"] == {
            "total": 1,
            "classes": 1,
            "by_class": {"circle": 1},
            "average_score": detection["score"],
            "score_type": "geometric_similarity",
        }

    def test_multiple_shapes_and_classes(self, client: TestClient) -> None:
        shapes, pixels = all_shapes_scene()

        response = client.post(DETECT_URL, files={"file": ("s.jpg", encode(pixels, ".jpg"))})

        body = response.json()
        assert response.status_code == 200
        assert body["summary"]["total"] == len(shapes)
        assert body["summary"]["classes"] == 6
        assert body["summary"]["by_class"] == dict.fromkeys(
            ["circle", "triangle", "square", "rectangle", "pentagon", "hexagon"], 1
        )
        assert [d["id"] for d in body["detections"]] == list(range(1, len(shapes) + 1))
        # Reading order: rows top-to-bottom.
        tops = [d["bbox"]["y1"] for d in body["detections"]]
        assert tops[:3] == sorted(tops[:3]) or max(tops[:3]) < min(tops[3:])

    def test_image_without_shapes_is_a_successful_empty_result(self, client: TestClient) -> None:
        response = client.post(
            DETECT_URL, files={"file": ("blank.webp", encode(render([]), ".webp"))}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["detections"] == []
        assert body["summary"] == {
            "total": 0,
            "classes": 0,
            "by_class": {},
            "average_score": None,
            "score_type": None,
        }
        assert body["annotated_image"].startswith("data:image/jpeg;base64,")

    def test_annotated_image_is_a_decodable_jpeg_data_url(self, client: TestClient) -> None:
        png = encode(render([ShapeSpec("square", (300, 300), 200)]))

        body = client.post(DETECT_URL, files={"file": ("sq.png", png)}).json()

        prefix, payload = body["annotated_image"].split(",", 1)
        assert prefix == "data:image/jpeg;base64"
        assert base64.b64decode(payload).startswith(b"\xff\xd8\xff")

    def test_ignores_misleading_filename_and_content_type(self, client: TestClient) -> None:
        png = encode(render([ShapeSpec("triangle", (300, 300), 150)]))

        response = client.post(DETECT_URL, files={"file": ("notes.txt", png, "text/plain")})

        assert response.status_code == 200
        assert response.json()["detections"][0]["class_name"] == "triangle"


class TestRejectedUploads:
    def test_missing_file_field(self, client: TestClient) -> None:
        response = client.post(DETECT_URL, data={"other": "value"})

        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "validation_error"
        assert body["error"]["details"][0]["field"] == "file"

    def test_empty_file(self, client: TestClient) -> None:
        response = client.post(DETECT_URL, files={"file": ("empty.png", b"", "image/png")})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "empty_file"

    def test_unsupported_format(self, client: TestClient) -> None:
        response = client.post(
            DETECT_URL, files={"file": ("image.png", b"GIF89a\x01\x00\x01\x00", "image/png")}
        )

        assert response.status_code == 415
        assert response.json()["error"]["code"] == "unsupported_format"

    def test_corrupted_image(self, client: TestClient) -> None:
        jpeg = encode(render([ShapeSpec("circle", (300, 300), 100)]), ".jpg")

        response = client.post(
            DETECT_URL, files={"file": ("broken.jpg", jpeg[: len(jpeg) // 3], "image/jpeg")}
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_image"

    def test_image_dimensions_too_large(self) -> None:
        settings = make_settings(max_image_width=500, max_image_height=500)
        with TestClient(create_app(settings)) as client:
            response = client.post(DETECT_URL, files={"file": ("big.png", encode(render([])))})

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "image_too_large"

    def test_error_body_includes_request_id(self, client: TestClient) -> None:
        response = client.post(DETECT_URL, files={"file": ("x.bin", b"\x00\x01", "image/png")})

        body = response.json()
        assert body["request_id"] == response.headers["X-Request-ID"]


class TestUploadSizeLimits:
    @pytest.fixture
    def small_limit_client(self) -> Iterator[TestClient]:
        # 20 KB file limit; the body limit adds 64 KB of multipart overhead on top.
        with TestClient(create_app(make_settings(max_file_size_mb=20 / 1024))) as client:
            yield client

    def test_file_over_limit_but_body_within_overhead(self, small_limit_client: TestClient) -> None:
        payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30 * 1024

        response = small_limit_client.post(DETECT_URL, files={"file": ("big.png", payload)})

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "file_too_large"

    def test_declared_content_length_over_limit(self, small_limit_client: TestClient) -> None:
        payload = b"\x00" * 200 * 1024

        response = small_limit_client.post(DETECT_URL, files={"file": ("big.png", payload)})

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "file_too_large"

    def test_streamed_body_without_content_length(self, small_limit_client: TestClient) -> None:
        def chunks() -> Iterator[bytes]:
            yield b'--boundary\r\nContent-Disposition: form-data; name="file"; '
            yield b'filename="a.png"\r\nContent-Type: image/png\r\n\r\n'
            for _ in range(20):
                yield b"\x00" * 10 * 1024

        response = small_limit_client.post(
            DETECT_URL,
            content=chunks(),
            headers={"Content-Type": "multipart/form-data; boundary=boundary"},
        )

        assert response.status_code == 413
        assert response.json()["error"]["code"] == "file_too_large"


class ExplodingUseCase:
    def execute(self, data: bytes) -> None:
        msg = "secret internal failure details"
        raise RuntimeError(msg)


def test_unexpected_errors_return_sanitised_500(app: FastAPI, settings: Settings) -> None:
    services: Services = app.state.services
    app.dependency_overrides[get_services] = lambda: Services(
        settings=settings,
        detect_shapes=ExplodingUseCase(),  # type: ignore[arg-type]
        detection_limiter=services.detection_limiter,
    )

    with TestClient(app) as client:
        response = client.post(
            DETECT_URL,
            files={"file": ("a.png", encode(render([])))},
            headers={"Origin": "http://localhost:3000"},
        )

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert "secret" not in response.text
    assert body["request_id"] == response.headers["X-Request-ID"]
    # The browser must be able to read the error, so CORS headers are present.
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
