import math

import numpy as np
import pytest

from app.infrastructure.detectors.opencv.features import interior_angles, measure_contour


def test_interior_angles_of_rectangle() -> None:
    vertices = np.array([[0, 0], [10, 0], [10, 5], [0, 5]], dtype=np.float64)

    assert interior_angles(vertices) == pytest.approx((90.0,) * 4)


def test_interior_angles_of_equilateral_triangle() -> None:
    vertices = np.array([[0, 0], [2, 0], [1, math.sqrt(3)]], dtype=np.float64)

    assert interior_angles(vertices) == pytest.approx((60.0,) * 3)


def test_degenerate_polygons_have_no_angles() -> None:
    assert interior_angles(np.array([[0, 0], [1, 1]], dtype=np.float64)) == ()
    assert interior_angles(np.array([[0, 0], [0, 0], [1, 1]], dtype=np.float64)) == ()


def test_measures_axis_aligned_rectangle_contour() -> None:
    contour = np.array([[[0, 0]], [[200, 0]], [[200, 100]], [[0, 100]]], dtype=np.int32)

    features = measure_contour(contour, approximation_factor=0.04)

    assert features is not None
    assert features.vertex_count == 4
    assert features.aspect_ratio == pytest.approx(0.5)
    assert features.solidity == pytest.approx(1.0)
    assert features.polygon_fit == pytest.approx(1.0)
    assert features.circularity == pytest.approx(4 * math.pi * 20_000 / 600**2)


def test_zero_area_contour_is_degenerate() -> None:
    line = np.array([[[0, 0]], [[50, 0]]], dtype=np.int32)

    assert measure_contour(line, approximation_factor=0.04) is None
