from dataclasses import dataclass, field

from app.domain.services import ClassificationRules
from app.infrastructure.detectors.opencv.regions import RegionMergeConfig


@dataclass(frozen=True, slots=True)
class OpenCVDetectorConfig:
    """Every tunable of the OpenCV pipeline, in one place.

    Attributes:
        min_contour_area: Smallest contour area to consider, in *original-image* pixels.
            It is rescaled automatically when the image is downscaled for processing.
        max_contour_area_ratio: Contours covering more than this fraction of the image
            are treated as background/frame and ignored.
        approximation_factor: ``approxPolyDP`` tolerance as a fraction of the perimeter.
        processing_max_dimension: Images are downscaled so their longest side is at most
            this many pixels before analysis; bounding boxes are mapped back afterwards.
        blur_kernel_size: Odd Gaussian kernel size used for noise reduction.
        canny_low_threshold: Canny hysteresis lower bound (per colour channel).
        canny_high_threshold: Canny hysteresis upper bound (per colour channel).
        morph_kernel_size: Kernel used to close small gaps in the edge map.
        duplicate_iou_threshold: Same-class detections overlapping at least this much
            are merged into one shape (edges of a shape yield inner and outer contours).
        outline_tolerance: Maximum deviation (original-image pixels) of a detection's
            traced outline from the shape's real boundary.
        region_merge: How faces split by crossing outlines are recombined into shapes.
        classification: Rules used to turn contour geometry into a shape class.
    """

    min_contour_area: float = 500.0
    max_contour_area_ratio: float = 0.95
    approximation_factor: float = 0.04
    processing_max_dimension: int = 1600
    blur_kernel_size: int = 5
    canny_low_threshold: int = 30
    canny_high_threshold: int = 100
    morph_kernel_size: int = 3
    duplicate_iou_threshold: float = 0.6
    outline_tolerance: float = 1.0
    region_merge: RegionMergeConfig = field(default_factory=RegionMergeConfig)
    classification: ClassificationRules = field(default_factory=ClassificationRules)

    def __post_init__(self) -> None:
        if self.blur_kernel_size % 2 == 0 or self.blur_kernel_size < 1:
            msg = "blur_kernel_size must be a positive odd integer"
            raise ValueError(msg)
        if not 0 < self.approximation_factor < 1:
            msg = "approximation_factor must be within (0, 1)"
            raise ValueError(msg)
        if self.canny_low_threshold >= self.canny_high_threshold:
            msg = "canny_low_threshold must be lower than canny_high_threshold"
            raise ValueError(msg)
