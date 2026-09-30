from dataclasses import dataclass

from app.domain.value_objects.bounding_box import BoundingBox


@dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class Outline:
    """Closed polygon tracing a shape, in pixel coordinates of the original image.

    For polygons the points are the shape's corners; for round shapes they sample the
    fitted curve densely enough to draw it smoothly.
    """

    points: tuple[Point, ...]

    def __post_init__(self) -> None:
        if len(self.points) < 3:
            msg = f"An outline needs at least 3 points, got {len(self.points)}"
            raise ValueError(msg)
        if any(point.x < 0 or point.y < 0 for point in self.points):
            msg = "Outline points must have non-negative coordinates"
            raise ValueError(msg)

    def bounding_box(self) -> BoundingBox:
        """Tightest box containing every point (``x2``/``y2`` exclusive)."""
        xs = [point.x for point in self.points]
        ys = [point.y for point in self.points]
        return BoundingBox(x1=min(xs), y1=min(ys), x2=max(xs) + 1, y2=max(ys) + 1)
