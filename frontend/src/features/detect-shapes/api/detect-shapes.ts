import { parseDetectionResponse, type DetectionResult } from "@/entities/detection";
import { requestJson } from "@/shared/api";

/** Large images on a cold server can take a while; fail clearly rather than hang. */
const DETECTION_TIMEOUT_MS = 60_000;

export type DetectShapesFn = (
  file: File,
  options?: { signal?: AbortSignal },
) => Promise<DetectionResult>;

export const detectShapes: DetectShapesFn = async (file, options = {}) => {
  const body = new FormData();
  body.append("file", file, file.name);
  const json = await requestJson("/api/v1/detect", {
    method: "POST",
    body,
    signal: options.signal,
    timeoutMs: DETECTION_TIMEOUT_MS,
  });
  return parseDetectionResponse(json);
};
