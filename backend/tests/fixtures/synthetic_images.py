"""Deterministic synthetic test images with known ground truth.

Generating fixtures in code keeps the repository free of binary blobs and makes each
test's intent explicit (which shape, where, how large, filled or outlined).
"""

import math
from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

ShapeName = Literal["circle", "triangle", "square", "rectangle", "pentagon", "hexagon"]
BGR = tuple[int, int, int]

WHITE: BGR = (255, 255, 255)
DARK: BGR = (30, 30, 30)
BLUE: BGR = (200, 90, 40)

_POLYGON_SIDES: dict[str, int] = {"triangle": 3, "pentagon": 5, "hexagon": 6}


@dataclass(frozen=True)
class ShapeSpec:
    """A shape to draw.

    ``size`` is the radius for circles/regular polygons and the width for squares and
    rectangles. Rectangles use ``aspect`` (height / width).
    """

    name: ShapeName
    center: tuple[int, int]
    size: int
    color: BGR = BLUE
    rotation_deg: float = 0.0
    thickness: int = -1  # -1 means filled
    aspect: float = 0.5

    def points(self) -> NDArray[np.int32]:
        cx, cy = self.center
        if self.name in ("square", "rectangle"):
            height = self.size if self.name == "square" else self.size * self.aspect
            box = cv2.boxPoints(((cx, cy), (self.size, height), self.rotation_deg))
            return np.round(box).astype(np.int32)
        sides = _POLYGON_SIDES[self.name]
        # Start at the top so triangles/pentagons point upwards.
        start = math.radians(self.rotation_deg) - math.pi / 2
        return np.array(
            [
                (
                    round(cx + self.size * math.cos(start + 2 * math.pi * i / sides)),
                    round(cy + self.size * math.sin(start + 2 * math.pi * i / sides)),
                )
                for i in range(sides)
            ],
            dtype=np.int32,
        )

    def expected_bbox(self) -> tuple[int, int, int, int]:
        if self.name == "circle":
            cx, cy = self.center
            return cx - self.size, cy - self.size, cx + self.size + 1, cy + self.size + 1
        points = self.points()
        x1, y1 = points.min(axis=0)
        x2, y2 = points.max(axis=0)
        return int(x1), int(y1), int(x2) + 1, int(y2) + 1


def render(
    shapes: list[ShapeSpec],
    *,
    width: int = 800,
    height: int = 600,
    background: BGR = WHITE,
    noise_sigma: float = 0.0,
    seed: int = 0,
) -> NDArray[np.uint8]:
    canvas = np.full((height, width, 3), background, dtype=np.uint8)
    for spec in shapes:
        if spec.name == "circle":
            cv2.circle(canvas, spec.center, spec.size, spec.color, spec.thickness, cv2.LINE_AA)
        elif spec.thickness < 0:
            cv2.fillPoly(canvas, [spec.points()], spec.color, cv2.LINE_AA)
        else:
            cv2.polylines(canvas, [spec.points()], True, spec.color, spec.thickness, cv2.LINE_AA)
    if noise_sigma > 0:
        rng = np.random.default_rng(seed)
        noise = rng.normal(0, noise_sigma, canvas.shape)
        canvas = np.clip(canvas.astype(np.float64) + noise, 0, 255).astype(np.uint8)
    return canvas


def encode(pixels: NDArray[np.uint8], extension: str = ".png") -> bytes:
    ok, buffer = cv2.imencode(extension, pixels)
    assert ok, f"failed to encode {extension}"
    return buffer.tobytes()


def all_shapes_scene() -> tuple[list[ShapeSpec], NDArray[np.uint8]]:
    """One of every supported class, well separated, on a white canvas."""
    shapes = [
        ShapeSpec("circle", (150, 150), 80, color=(60, 60, 220)),
        ShapeSpec("triangle", (400, 160), 90, color=(60, 180, 60)),
        ShapeSpec("square", (650, 150), 150, color=(200, 90, 40)),
        ShapeSpec("rectangle", (150, 430), 200, color=(30, 160, 220), aspect=0.5),
        ShapeSpec("pentagon", (400, 440), 90, color=(160, 60, 160)),
        ShapeSpec("hexagon", (650, 440), 90, color=(120, 120, 20)),
    ]
    return shapes, render(shapes)
