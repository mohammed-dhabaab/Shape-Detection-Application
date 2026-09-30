import { describe, expect, it } from "vitest";

import { ApiError } from "@/shared/api";
import { detectionResponseDto, detectionResult } from "@/test/fixtures";

import { parseDetectionResponse } from "./parse-detection-response";

describe("parseDetectionResponse", () => {
  it("maps the snake_case contract to domain types", () => {
    expect(parseDetectionResponse(detectionResponseDto())).toEqual(detectionResult());
  });

  it("accepts an empty result", () => {
    const parsed = parseDetectionResponse(
      detectionResponseDto({
        detections: [],
        summary: { total: 0, classes: 0, by_class: {}, average_score: null, score_type: null },
      }),
    );

    expect(parsed.detections).toEqual([]);
    expect(parsed.summary).toEqual({
      total: 0,
      classes: 0,
      byClass: {},
      averageScore: null,
      scoreType: null,
    });
  });

  it("preserves the model_confidence score type", () => {
    const dto = detectionResponseDto();
    dto.detections[0]!.score_type = "model_confidence";

    expect(parseDetectionResponse(dto).detections[0]!.scoreType).toBe("model_confidence");
  });

  it.each([
    ["null body", null],
    ["missing detections", { ...detectionResponseDto(), detections: undefined }],
    ["unknown shape class", mutate((dto) => (dto.detections[0]!.class_name = "octagon"))],
    ["score out of range", mutate((dto) => (dto.detections[0]!.score = 1.5))],
    ["unknown score type", mutate((dto) => (dto.detections[0]!.score_type = "vibes"))],
    ["inverted bounding box", mutate((dto) => (dto.detections[0]!.bbox.x2 = 10))],
    ["non-data annotated image", { ...detectionResponseDto(), annotated_image: "https://x" }],
  ])("rejects a malformed response: %s", (_, body) => {
    expect(() => parseDetectionResponse(body)).toThrow(ApiError);
    try {
      parseDetectionResponse(body);
    } catch (error) {
      expect((error as ApiError).kind).toBe("invalid_response");
    }
  });
});

function mutate(change: (dto: ReturnType<typeof detectionResponseDto>) => void) {
  const dto = detectionResponseDto();
  change(dto);
  return dto;
}
