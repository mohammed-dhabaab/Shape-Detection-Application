"""Public contract of ``POST /api/v1/detect``.

These models are deliberately separate from the domain entities so internal
refactoring never silently changes the API shape.
"""

import base64
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from app.application.dto import DetectShapesOutput, EncodedImage
from app.domain.entities import Detection, DetectionSummary, ShapeType
from app.domain.value_objects import ScoreType


class _Schema(BaseModel):
    model_config = ConfigDict(frozen=True)


class ImageInfo(_Schema):
    width: int = Field(gt=0, examples=[1920])
    height: int = Field(gt=0, examples=[1080])


class BoundingBoxSchema(_Schema):
    """Pixel coordinates in the original image; ``x2``/``y2`` are exclusive."""

    x1: int = Field(ge=0, examples=[120])
    y1: int = Field(ge=0, examples=[80])
    x2: int = Field(gt=0, examples=[420])
    y2: int = Field(gt=0, examples=[380])


class DetectionSchema(_Schema):
    id: int = Field(ge=1, description="1-based, in reading order (top-to-bottom, left-to-right).")
    class_name: ShapeType
    score: float = Field(ge=0, le=1, examples=[0.94])
    score_type: ScoreType = Field(
        description=(
            "`geometric_similarity`: how closely the contour matches the ideal shape "
            "(classical CV). `model_confidence`: a trained model's confidence."
        )
    )
    bbox: BoundingBoxSchema
    outline: list[tuple[int, int]] | None = Field(
        default=None,
        description=(
            "Closed polygon tracing the shape's actual boundary, as `[x, y]` pixel "
            "coordinates of the original image (within 1 px of the real edge). `null` "
            "when the detector only produces boxes."
        ),
        examples=[[[120, 80], [420, 80], [420, 380], [120, 380]]],
    )

    @classmethod
    def from_domain(cls, detection_id: int, detection: Detection) -> Self:
        bbox = detection.bbox
        outline = detection.outline
        return cls(
            id=detection_id,
            class_name=detection.shape,
            score=detection.score.value,
            score_type=detection.score.type,
            bbox=BoundingBoxSchema(x1=bbox.x1, y1=bbox.y1, x2=bbox.x2, y2=bbox.y2),
            outline=[(p.x, p.y) for p in outline.points] if outline is not None else None,
        )


class SummarySchema(_Schema):
    total: int = Field(ge=0)
    classes: int = Field(ge=0, description="Number of distinct shape classes detected.")
    by_class: dict[ShapeType, int]
    average_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Mean score, or null when there are no detections or mixed score types.",
    )
    score_type: ScoreType | None = None

    @classmethod
    def from_domain(cls, summary: DetectionSummary) -> Self:
        return cls(
            total=summary.total,
            classes=summary.classes,
            by_class=summary.by_class,
            average_score=(
                round(summary.average_score, 4) if summary.average_score is not None else None
            ),
            score_type=summary.score_type,
        )


class DetectionResponse(_Schema):
    image: ImageInfo
    detections: list[DetectionSchema]
    summary: SummarySchema
    annotated_image: str = Field(
        description="Annotated image as a data URL (e.g. `data:image/jpeg;base64,...`).",
    )

    @classmethod
    def from_output(cls, output: DetectShapesOutput) -> Self:
        result = output.result
        return cls(
            image=ImageInfo(width=result.image_size.width, height=result.image_size.height),
            detections=[
                DetectionSchema.from_domain(index, detection)
                for index, detection in enumerate(result.detections, start=1)
            ],
            summary=SummarySchema.from_domain(result.summary),
            annotated_image=_to_data_url(output.annotated_image),
        )


def _to_data_url(image: EncodedImage) -> str:
    encoded = base64.b64encode(image.data).decode("ascii")
    return f"data:{image.media_type};base64,{encoded}"
