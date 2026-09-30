from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Axis-aligned box in pixel coordinates of the original image.

    ``(x1, y1)`` is the inclusive top-left corner and ``(x2, y2)`` the exclusive
    bottom-right corner, so ``width == x2 - x1``.
    """

    x1: int
    y1: int
    x2: int
    y2: int

    def __post_init__(self) -> None:
        if self.x1 < 0 or self.y1 < 0:
            msg = f"Bounding box origin must be non-negative, got ({self.x1}, {self.y1})"
            raise ValueError(msg)
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            msg = f"Bounding box must have positive size, got {self}"
            raise ValueError(msg)

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def area(self) -> int:
        return self.width * self.height

    def intersection_area(self, other: "BoundingBox") -> int:
        width = min(self.x2, other.x2) - max(self.x1, other.x1)
        height = min(self.y2, other.y2) - max(self.y1, other.y1)
        return max(width, 0) * max(height, 0)

    def enclosing(self, other: "BoundingBox") -> "BoundingBox":
        """Smallest box containing both boxes."""
        return BoundingBox(
            x1=min(self.x1, other.x1),
            y1=min(self.y1, other.y1),
            x2=max(self.x2, other.x2),
            y2=max(self.y2, other.y2),
        )

    def iou(self, other: "BoundingBox") -> float:
        """Intersection over union, in ``[0, 1]``."""
        intersection = self.intersection_area(other)
        union = self.area + other.area - intersection
        return intersection / union
