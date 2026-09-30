from dataclasses import dataclass

from app.application.dto.images import EncodedImage
from app.domain.entities import DetectionResult


@dataclass(frozen=True, slots=True)
class DetectShapesOutput:
    result: DetectionResult
    annotated_image: EncodedImage
