export type {
  BoundingBoxDto,
  DetectionDto,
  DetectionResponseDto,
  DetectionSummaryDto,
} from "./api/dto";
export { parseDetectionResponse } from "./api/parse-detection-response";
export { SCORE_TYPE_META, formatScore, type ScoreTypeMeta } from "./lib/score";
export { SHAPE_META, orderedClassCounts, shapeCountLabel, type ShapeMeta } from "./lib/shape-meta";
export {
  SCORE_TYPES,
  SHAPE_CLASSES,
  type BoundingBox,
  type Detection,
  type DetectionResult,
  type DetectionSummary,
  type ScoreType,
  type ShapeClass,
} from "./model/types";
export { DetectionItem } from "./ui/DetectionItem";
export { ShapeBadge } from "./ui/ShapeBadge";
