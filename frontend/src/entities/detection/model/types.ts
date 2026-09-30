/** Domain types for detection results, decoupled from the wire format (see `api/dto.ts`). */

export const SHAPE_CLASSES = [
  "circle",
  "ellipse",
  "triangle",
  "square",
  "rectangle",
  "pentagon",
  "hexagon",
] as const;

export type ShapeClass = (typeof SHAPE_CLASSES)[number];

export const SCORE_TYPES = ["geometric_similarity", "model_confidence"] as const;

/**
 * What a score measures. Geometric similarity (classical CV) and model confidence
 * (a trained detector) are not interchangeable and must be labelled distinctly.
 */
export type ScoreType = (typeof SCORE_TYPES)[number];

export interface BoundingBox {
  /** Inclusive left edge, in original-image pixels. */
  x1: number;
  /** Inclusive top edge. */
  y1: number;
  /** Exclusive right edge. */
  x2: number;
  /** Exclusive bottom edge. */
  y2: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface Detection {
  /** 1-based, in reading order; matches the "#n" label drawn on the annotated image. */
  id: number;
  shape: ShapeClass;
  score: number;
  scoreType: ScoreType;
  bbox: BoundingBox;
  /**
   * Closed polygon tracing the shape's actual boundary, in original-image pixels.
   * `null` when the detector only reports boxes.
   */
  outline: Point[] | null;
}

export interface DetectionSummary {
  total: number;
  classes: number;
  byClass: Partial<Record<ShapeClass, number>>;
  /** `null` when there are no detections or the score types are mixed. */
  averageScore: number | null;
  scoreType: ScoreType | null;
}

export interface DetectionResult {
  image: { width: number; height: number };
  detections: Detection[];
  summary: DetectionSummary;
  /** Annotated image as a `data:` URL. */
  annotatedImageUrl: string;
}
