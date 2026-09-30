import pytest
from pydantic import ValidationError

from tests.conftest import make_settings


def test_parses_comma_separated_origins() -> None:
    settings = make_settings(allowed_origins="http://localhost:3000, https://shapes.example.com/")

    assert settings.allowed_origins == ["http://localhost:3000", "https://shapes.example.com"]


def test_reads_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "5")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.example,https://b.example")
    monkeypatch.setenv("MIN_CONTOUR_AREA", "750")

    settings = make_settings()

    assert settings.max_file_size_bytes == 5 * 1024 * 1024
    assert settings.min_contour_area == 750
    # Explicit overrides in make_settings win over the environment.
    assert settings.allowed_origins == ["http://localhost:3000"]


def test_rejects_wildcard_origin_in_production() -> None:
    with pytest.raises(ValidationError, match="Wildcard"):
        make_settings(environment="production", allowed_origins="*")


def test_rejects_inconsistent_canny_thresholds() -> None:
    with pytest.raises(ValidationError, match="CANNY"):
        make_settings(canny_low_threshold=120, canny_high_threshold=100)


@pytest.mark.parametrize(
    ("field", "value"),
    [("max_file_size_mb", 0), ("contour_approximation_factor", 1.5), ("min_detection_score", 2)],
)
def test_rejects_out_of_range_values(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        make_settings(**{field: value})
