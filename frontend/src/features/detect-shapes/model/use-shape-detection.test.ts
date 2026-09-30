import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { DetectionResult } from "@/entities/detection";
import { ApiError } from "@/shared/api";
import { deferred, detectionResult, pngFile } from "@/test/fixtures";

import type { DetectShapesFn } from "../api/detect-shapes";

import { useShapeDetection } from "./use-shape-detection";

function controllableDetect() {
  const calls: Array<{
    signal?: AbortSignal;
    request: ReturnType<typeof deferred<DetectionResult>>;
  }> = [];
  const detect: DetectShapesFn = vi.fn((_file, options) => {
    const request = deferred<DetectionResult>();
    calls.push({ signal: options?.signal, request });
    return request.promise;
  });
  return { detect, calls };
}

describe("useShapeDetection", () => {
  it("moves from idle to processing to success", async () => {
    const { detect, calls } = controllableDetect();
    const { result } = renderHook(() => useShapeDetection(detect));
    expect(result.current.state).toEqual({ status: "idle" });

    let run!: Promise<void>;
    act(() => {
      run = result.current.run(pngFile());
    });
    expect(result.current.state).toEqual({ status: "processing" });

    await act(async () => {
      calls[0]!.request.resolve(detectionResult());
      await run;
    });
    expect(result.current.state).toEqual({ status: "success", result: detectionResult() });
  });

  it("surfaces API failures as an error state", async () => {
    const { detect, calls } = controllableDetect();
    const { result } = renderHook(() => useShapeDetection(detect));
    const failure = new ApiError({ kind: "network" });

    await act(async () => {
      const run = result.current.run(pngFile());
      calls[0]!.request.reject(failure);
      await run;
    });

    expect(result.current.state).toEqual({ status: "error", error: failure });
  });

  it("wraps unexpected exceptions in an ApiError", async () => {
    const detect: DetectShapesFn = vi.fn(async () => {
      throw new Error("boom");
    });
    const { result } = renderHook(() => useShapeDetection(detect));

    await act(() => result.current.run(pngFile()));

    expect(result.current.state.status).toBe("error");
  });

  it("ignores duplicate submissions while a request is in flight", async () => {
    const { detect } = controllableDetect();
    const { result } = renderHook(() => useShapeDetection(detect));

    act(() => {
      void result.current.run(pngFile());
      void result.current.run(pngFile());
    });

    expect(detect).toHaveBeenCalledTimes(1);
  });

  it("reset aborts the request and ignores its late response", async () => {
    const { detect, calls } = controllableDetect();
    const { result } = renderHook(() => useShapeDetection(detect));

    let run!: Promise<void>;
    act(() => {
      run = result.current.run(pngFile());
    });
    act(() => result.current.reset());
    expect(calls[0]!.signal?.aborted).toBe(true);

    await act(async () => {
      calls[0]!.request.resolve(detectionResult());
      await run;
    });
    expect(result.current.state).toEqual({ status: "idle" });
  });

  it("aborts the in-flight request on unmount", () => {
    const { detect, calls } = controllableDetect();
    const { result, unmount } = renderHook(() => useShapeDetection(detect));

    act(() => {
      void result.current.run(pngFile());
    });
    unmount();

    expect(calls[0]!.signal?.aborted).toBe(true);
  });
});
