import { describe, expect, it } from "vitest";

import { formatScore } from "./score";
import { orderedClassCounts, shapeCountLabel } from "./shape-meta";

describe("formatScore", () => {
  it("labels geometric similarity explicitly", () => {
    expect(formatScore(0.936, "geometric_similarity")).toBe("94% geometric similarity");
  });

  it("labels model confidence differently", () => {
    expect(formatScore(0.5, "model_confidence")).toBe("50% model confidence");
  });
});

describe("shape metadata helpers", () => {
  it("orders class counts canonically and skips absent classes", () => {
    expect(orderedClassCounts({ hexagon: 1, circle: 3, square: 0 })).toEqual([
      { shape: "circle", count: 3 },
      { shape: "hexagon", count: 1 },
    ]);
  });

  it("pluralises shape labels", () => {
    expect(shapeCountLabel("circle", 1)).toBe("1 circle");
    expect(shapeCountLabel("circle", 2)).toBe("2 circles");
  });
});
