/**
 * Wire format of `POST /api/v1/detect`, mirroring the backend's Pydantic schemas
 * (backend/app/schemas/detection.py). Kept separate from the domain types so a
 * contract change is handled in one mapper instead of leaking through the UI.
 */

export interface BoundingBoxDto {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface DetectionDto {
  id: number;
  class_name: string;
  score: number;
  score_type: string;
  bbox: BoundingBoxDto;
  /** `[x, y]` pairs; absent or null for box-only detectors. */
  outline?: Array<[number, number]> | null;
}

export interface DetectionSummaryDto {
  total: number;
  classes: number;
  by_class: Record<string, number>;
  average_score: number | null;
  score_type: string | null;
}

export interface DetectionResponseDto {
  image: { width: number; height: number };
  detections: DetectionDto[];
  summary: DetectionSummaryDto;
  annotated_image: string;
}
