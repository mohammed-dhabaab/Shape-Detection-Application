import logging
import time
from collections.abc import Iterable

from app.application.dto import DetectShapesOutput
from app.application.errors import EmptyFileError
from app.application.ports import ImageAnnotator, ImageDecoder, ShapeDetector
from app.domain.entities import Detection, DetectionResult

logger = logging.getLogger(__name__)


class DetectShapes:
    """Use case: analyse an uploaded image and report the shapes it contains."""

    def __init__(
        self,
        decoder: ImageDecoder,
        detector: ShapeDetector,
        annotator: ImageAnnotator,
    ) -> None:
        self._decoder = decoder
        self._detector = detector
        self._annotator = annotator

    def execute(self, data: bytes) -> DetectShapesOutput:
        if not data:
            raise EmptyFileError

        started = time.perf_counter()
        image = self._decoder.decode(data)
        detections = in_reading_order(self._detector.detect(image))
        result = DetectionResult(image_size=image.size, detections=detections)
        annotated = self._annotator.annotate(image, result.detections)

        logger.info(
            "Shape detection completed",
            extra={
                "image_width": result.image_size.width,
                "image_height": result.image_size.height,
                "detections": result.summary.total,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return DetectShapesOutput(result=result, annotated_image=annotated)


def in_reading_order(detections: Iterable[Detection]) -> tuple[Detection, ...]:
    """Order detections like text: rows top-to-bottom, each row left-to-right.

    A detection joins the current row when its top edge lies above the vertical centre
    of the row's first (top-most) detection, so shapes that sit side by side are
    numbered left-to-right even if their top edges differ by a few pixels. This keeps
    detection IDs stable and intuitive when matching labels to the image.
    """
    rows: list[list[Detection]] = []
    for detection in sorted(detections, key=lambda item: item.bbox.y1):
        if rows and detection.bbox.y1 < _vertical_centre(rows[-1][0]):
            rows[-1].append(detection)
        else:
            rows.append([detection])
    return tuple(
        detection for row in rows for detection in sorted(row, key=lambda item: item.bbox.x1)
    )


def _vertical_centre(detection: Detection) -> float:
    return (detection.bbox.y1 + detection.bbox.y2) / 2
