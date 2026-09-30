/**
 * Test-only fixtures shared across slices. Lives outside the FSD layers on purpose:
 * it is tooling, not application code.
 */
import type { DetectionResponseDto, DetectionResult } from "@/entities/detection";

const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const JPEG_SIGNATURE = [0xff, 0xd8, 0xff, 0xe0];

export function pngFile(name = "shapes.png", extraBytes = 64): File {
  return new File([new Uint8Array([...PNG_SIGNATURE, ...new Array(extraBytes).fill(0)])], name, {
    type: "image/png",
  });
}

export function jpegFile(name = "photo.jpg"): File {
  return new File([new Uint8Array([...JPEG_SIGNATURE, ...new Array(64).fill(0)])], name, {
    type: "image/jpeg",
  });
}

export function textFile(name = "notes.png"): File {
  // Misleading extension and MIME type: content sniffing must reject it.
  return new File(["just some text, not an image"], name, { type: "image/png" });
}

export function detectionResponseDto(
  overrides: Partial<DetectionResponseDto> = {},
): DetectionResponseDto {
  return {
    image: { width: 800, height: 600 },
    detections: [
      {
        id: 1,
        class_name: "circle",
        score: 0.94,
        score_type: "geometric_similarity",
        bbox: { x1: 120, y1: 80, x2: 420, y2: 380 },
      },
      {
        id: 2,
        class_name: "triangle",
        score: 0.9,
        score_type: "geometric_similarity",
        bbox: { x1: 500, y1: 100, x2: 700, y2: 280 },
      },
    ],
    summary: {
      total: 2,
      classes: 2,
      by_class: { circle: 1, triangle: 1 },
      average_score: 0.92,
      score_type: "geometric_similarity",
    },
    annotated_image: "data:image/jpeg;base64,AAAA",
    ...overrides,
  };
}

export function detectionResult(overrides: Partial<DetectionResult> = {}): DetectionResult {
  return {
    image: { width: 800, height: 600 },
    detections: [
      {
        id: 1,
        shape: "circle",
        score: 0.94,
        scoreType: "geometric_similarity",
        bbox: { x1: 120, y1: 80, x2: 420, y2: 380 },
      },
      {
        id: 2,
        shape: "triangle",
        score: 0.9,
        scoreType: "geometric_similarity",
        bbox: { x1: 500, y1: 100, x2: 700, y2: 280 },
      },
    ],
    summary: {
      total: 2,
      classes: 2,
      byClass: { circle: 1, triangle: 1 },
      averageScore: 0.92,
      scoreType: "geometric_similarity",
    },
    annotatedImageUrl: "data:image/jpeg;base64,AAAA",
    ...overrides,
  };
}

export function emptyDetectionResult(): DetectionResult {
  return detectionResult({
    detections: [],
    summary: { total: 0, classes: 0, byClass: {}, averageScore: null, scoreType: null },
  });
}

/** A promise you can settle from the test, for controlling async timing precisely. */
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}
