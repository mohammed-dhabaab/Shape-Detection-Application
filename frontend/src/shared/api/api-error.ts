/** Every way a request to the backend can fail, as a discriminated union. */
export type ApiErrorDetail =
  | { kind: "network" }
  | { kind: "timeout"; timeoutMs: number }
  | { kind: "aborted" }
  | {
      kind: "http";
      status: number;
      /** Stable machine-readable code from the backend error envelope. */
      code: string;
      /** Human-readable message from the backend, safe to display. */
      message: string;
      requestId?: string;
    }
  | { kind: "invalid_response"; reason: string };

export type ApiErrorKind = ApiErrorDetail["kind"];

function describe(detail: ApiErrorDetail): string {
  switch (detail.kind) {
    case "network":
      return "Network request failed";
    case "timeout":
      return `Request timed out after ${detail.timeoutMs} ms`;
    case "aborted":
      return "Request was cancelled";
    case "http":
      return `HTTP ${detail.status} (${detail.code}): ${detail.message}`;
    case "invalid_response":
      return `Invalid response: ${detail.reason}`;
  }
}

export class ApiError extends Error {
  readonly detail: ApiErrorDetail;

  constructor(detail: ApiErrorDetail, options?: { cause?: unknown }) {
    super(describe(detail), options);
    this.name = "ApiError";
    this.detail = detail;
  }

  get kind(): ApiErrorKind {
    return this.detail.kind;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
