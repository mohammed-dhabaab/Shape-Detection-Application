import { ApiError } from "@/shared/api";

import {
  SCORE_TYPES,
  SHAPE_CLASSES,
  type BoundingBox,
  type Detection,
  type DetectionResult,
  type ScoreType,
  type ShapeClass,
} from "../model/types";

import type { BoundingBoxDto, DetectionDto, DetectionResponseDto } from "./dto";

/**
 * Validates an untrusted JSON body against the detection contract and maps it to
 * domain types. A small hand-written guard is enough for one endpoint and avoids
 * pulling in a schema library.
 *
 * @throws {ApiError} with kind `invalid_response` when the body does not match.
 */
export function parseDetectionResponse(body: unknown): DetectionResult {
  if (!isDetectionResponseDto(body)) {
    throw new ApiError({
      kind: "invalid_response",
      reason: "Detection response does not match the expected contract",
    });
  }

  const byClass: DetectionResult["summary"]["byClass"] = {};
  for (const [name, count] of Object.entries(body.summary.by_class)) {
    if (isShapeClass(name)) byClass[name] = count;
  }

  return {
    image: { width: body.image.width, height: body.image.height },
    detections: body.detections.map(toDetection),
    summary: {
      total: body.summary.total,
      classes: body.summary.classes,
      byClass,
      averageScore: body.summary.average_score,
      scoreType: isScoreType(body.summary.score_type) ? body.summary.score_type : null,
    },
    annotatedImageUrl: body.annotated_image,
  };
}

function toDetection(dto: DetectionDto): Detection {
  return {
    id: dto.id,
    // Guarded by isDetectionDto.
    shape: dto.class_name as ShapeClass,
    score: dto.score,
    scoreType: dto.score_type as ScoreType,
    bbox: toBoundingBox(dto.bbox),
  };
}

function toBoundingBox({ x1, y1, x2, y2 }: BoundingBoxDto): BoundingBox {
  return { x1, y1, x2, y2 };
}

function isDetectionResponseDto(value: unknown): value is DetectionResponseDto {
  if (!isRecord(value) || !isRecord(value.image) || !isRecord(value.summary)) return false;
  const { image, summary } = value;
  return (
    isPositiveInteger(image.width) &&
    isPositiveInteger(image.height) &&
    Array.isArray(value.detections) &&
    value.detections.every(isDetectionDto) &&
    isNonNegativeInteger(summary.total) &&
    isNonNegativeInteger(summary.classes) &&
    isRecord(summary.by_class) &&
    Object.values(summary.by_class).every(isNonNegativeInteger) &&
    (summary.average_score === null ||
      summary.average_score === undefined ||
      isUnitInterval(summary.average_score)) &&
    typeof value.annotated_image === "string" &&
    value.annotated_image.startsWith("data:image/")
  );
}

function isDetectionDto(value: unknown): value is DetectionDto {
  return (
    isRecord(value) &&
    isPositiveInteger(value.id) &&
    isShapeClass(value.class_name) &&
    isUnitInterval(value.score) &&
    isScoreType(value.score_type) &&
    isBoundingBoxDto(value.bbox)
  );
}

function isBoundingBoxDto(value: unknown): value is BoundingBoxDto {
  return (
    isRecord(value) &&
    isNonNegativeInteger(value.x1) &&
    isNonNegativeInteger(value.y1) &&
    isNonNegativeInteger(value.x2) &&
    isNonNegativeInteger(value.y2) &&
    value.x2 > value.x1 &&
    value.y2 > value.y1
  );
}

function isShapeClass(value: unknown): value is ShapeClass {
  return typeof value === "string" && (SHAPE_CLASSES as readonly string[]).includes(value);
}

function isScoreType(value: unknown): value is ScoreType {
  return typeof value === "string" && (SCORE_TYPES as readonly string[]).includes(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isPositiveInteger(value: unknown): value is number {
  return isNonNegativeInteger(value) && value > 0;
}

function isUnitInterval(value: unknown): value is number {
  return typeof value === "number" && value >= 0 && value <= 1;
}
