from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field

from app.domain.entities.shape import ShapeType
from app.domain.value_objects import BoundingBox, DetectionScore, ImageSize, ScoreType


@dataclass(frozen=True, slots=True)
class Detection:
    """A single shape found in an image, independent of how it was found."""

    shape: ShapeType
    bbox: BoundingBox
    score: DetectionScore


@dataclass(frozen=True, slots=True)
class DetectionSummary:
    total: int
    by_class: dict[ShapeType, int]
    average_score: float | None
    score_type: ScoreType | None

    @property
    def classes(self) -> int:
        return len(self.by_class)

    @classmethod
    def from_detections(cls, detections: Iterable[Detection]) -> "DetectionSummary":
        items = tuple(detections)
        counts = Counter(detection.shape for detection in items)
        # Preserve the enum's declaration order so summaries are deterministic.
        by_class = {shape: counts[shape] for shape in ShapeType if counts[shape]}

        score_types = {detection.score.type for detection in items}
        # Averaging scores with different semantics would be meaningless.
        if len(score_types) == 1:
            (score_type,) = score_types
            average = sum(detection.score.value for detection in items) / len(items)
        else:
            score_type, average = None, None

        return cls(
            total=len(items),
            by_class=by_class,
            average_score=average,
            score_type=score_type,
        )


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Outcome of analysing one image. An empty result is a valid, successful outcome."""

    image_size: ImageSize
    detections: tuple[Detection, ...]
    summary: DetectionSummary = field(init=False)

    def __post_init__(self) -> None:
        for detection in self.detections:
            bbox = detection.bbox
            if bbox.x2 > self.image_size.width or bbox.y2 > self.image_size.height:
                msg = f"Bounding box {bbox} exceeds image bounds {self.image_size}"
                raise ValueError(msg)
        object.__setattr__(self, "summary", DetectionSummary.from_detections(self.detections))
