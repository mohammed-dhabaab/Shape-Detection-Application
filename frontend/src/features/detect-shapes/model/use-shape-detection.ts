"use client";

import { useCallback, useEffect, useReducer, useRef } from "react";

import type { DetectionResult } from "@/entities/detection";
import { ApiError, isApiError } from "@/shared/api";

import { detectShapes, type DetectShapesFn } from "../api/detect-shapes";

export type DetectionState =
  | { status: "idle" }
  | { status: "processing" }
  | { status: "success"; result: DetectionResult }
  | { status: "error"; error: ApiError };

type DetectionAction =
  | { type: "started" }
  | { type: "succeeded"; result: DetectionResult }
  | { type: "failed"; error: ApiError }
  | { type: "reset" };

const IDLE: DetectionState = { status: "idle" };

export function detectionReducer(state: DetectionState, action: DetectionAction): DetectionState {
  switch (action.type) {
    case "started":
      return { status: "processing" };
    case "succeeded":
      return state.status === "processing" ? { status: "success", result: action.result } : state;
    case "failed":
      return state.status === "processing" ? { status: "error", error: action.error } : state;
    case "reset":
      return IDLE;
  }
}

export interface ShapeDetection {
  state: DetectionState;
  /** Starts detection. Ignored while a request is already in flight. */
  run: (file: File) => Promise<void>;
  /** Cancels any in-flight request and returns to idle. */
  reset: () => void;
}

/**
 * Owns the detect-shapes workflow: `idle → processing → success | error`.
 *
 * Only one request runs at a time. Resetting (or unmounting) aborts it, and a
 * response that arrives after its request was cancelled is ignored, so stale results
 * can never overwrite newer state.
 */
export function useShapeDetection(detect: DetectShapesFn = detectShapes): ShapeDetection {
  const [state, dispatch] = useReducer(detectionReducer, IDLE);
  const inFlight = useRef<AbortController | null>(null);

  useEffect(() => () => inFlight.current?.abort(), []);

  const run = useCallback(
    async (file: File) => {
      if (inFlight.current) return;
      const controller = new AbortController();
      inFlight.current = controller;
      dispatch({ type: "started" });

      try {
        const result = await detect(file, { signal: controller.signal });
        if (!controller.signal.aborted) dispatch({ type: "succeeded", result });
      } catch (error) {
        if (!controller.signal.aborted) dispatch({ type: "failed", error: toApiError(error) });
      } finally {
        if (inFlight.current === controller) inFlight.current = null;
      }
    },
    [detect],
  );

  const reset = useCallback(() => {
    inFlight.current?.abort();
    inFlight.current = null;
    dispatch({ type: "reset" });
  }, []);

  return { state, run, reset };
}

function toApiError(error: unknown): ApiError {
  if (isApiError(error)) return error;
  return new ApiError(
    { kind: "invalid_response", reason: error instanceof Error ? error.message : String(error) },
    { cause: error },
  );
}
