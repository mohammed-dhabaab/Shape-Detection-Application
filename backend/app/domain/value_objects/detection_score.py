from dataclasses import dataclass
from enum import StrEnum


class ScoreType(StrEnum):
    """What a detection score measures.

    Scores of different types are not comparable: a geometric similarity of 0.9 says
    the contour closely matches the ideal shape, while a model confidence of 0.9 is a
    learned probability-like output.
    """

    GEOMETRIC_SIMILARITY = "geometric_similarity"
    MODEL_CONFIDENCE = "model_confidence"


@dataclass(frozen=True, slots=True)
class DetectionScore:
    value: float
    type: ScoreType

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            msg = f"Detection score must be within [0, 1], got {self.value}"
            raise ValueError(msg)
