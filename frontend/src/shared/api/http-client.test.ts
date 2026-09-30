import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api-error";
import { requestJson } from "./http-client";

function mockFetch(implementation: typeof fetch) {
  const fetchMock = vi.fn(implementation);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

async function captureError(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError);
    return error as ApiError;
  }
  throw new Error("Expected the request to fail");
}

describe("requestJson", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("resolves with the parsed body and targets the configured API", async () => {
    const fetchMock = mockFetch(async () => jsonResponse({ status: "ok" }));

    await expect(requestJson("/api/v1/health")).resolves.toEqual({ status: "ok" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/health",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("maps the backend error envelope to an http error", async () => {
    mockFetch(async () =>
      jsonResponse(
        {
          error: { code: "unsupported_format", message: "Unsupported file type." },
          request_id: "abc",
        },
        { status: 415 },
      ),
    );

    const error = await captureError(requestJson("/api/v1/detect", { method: "POST" }));

    expect(error.detail).toEqual({
      kind: "http",
      status: 415,
      code: "unsupported_format",
      message: "Unsupported file type.",
      requestId: "abc",
    });
  });

  it("still reports an http error when the error body is not JSON", async () => {
    mockFetch(
      async () => new Response("<h1>Bad gateway</h1>", { status: 502, statusText: "Bad Gateway" }),
    );

    const error = await captureError(requestJson("/x"));

    expect(error.detail).toMatchObject({ kind: "http", status: 502, code: "http_502" });
  });

  it("reports network failures", async () => {
    mockFetch(async () => {
      throw new TypeError("Failed to fetch");
    });

    expect((await captureError(requestJson("/x"))).kind).toBe("network");
  });

  it("reports caller cancellation as aborted", async () => {
    const controller = new AbortController();
    mockFetch(async (_, init) => {
      controller.abort();
      throw init?.signal?.reason ?? new DOMException("Aborted", "AbortError");
    });

    const error = await captureError(requestJson("/x", { signal: controller.signal }));

    expect(error.kind).toBe("aborted");
  });

  it("reports invalid JSON on success as invalid_response", async () => {
    mockFetch(async () => new Response("not json", { status: 200 }));

    expect((await captureError(requestJson("/x"))).kind).toBe("invalid_response");
  });
});
