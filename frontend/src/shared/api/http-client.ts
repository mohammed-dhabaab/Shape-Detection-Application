import { env } from "@/shared/config";

import { ApiError, type ApiErrorDetail } from "./api-error";

const DEFAULT_TIMEOUT_MS = 60_000;

export interface RequestOptions {
  method?: "GET" | "POST";
  body?: BodyInit;
  /** Caller-controlled cancellation (e.g. the user resets or unmounts). */
  signal?: AbortSignal;
  timeoutMs?: number;
}

/**
 * Performs a request against the backend and resolves with the parsed JSON body.
 *
 * Every failure is normalised into an {@link ApiError}, so callers handle one error
 * type with an exhaustive `kind` instead of a mix of `TypeError`, `DOMException` and
 * non-2xx responses. Response validation belongs to the caller, which knows the
 * expected shape.
 */
export async function requestJson(path: string, options: RequestOptions = {}): Promise<unknown> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const timeoutSignal = AbortSignal.timeout(timeoutMs);
  const signal = options.signal ? AbortSignal.any([options.signal, timeoutSignal]) : timeoutSignal;

  const toTransportError = (cause: unknown): ApiError => {
    if (options.signal?.aborted) return new ApiError({ kind: "aborted" }, { cause });
    if (timeoutSignal.aborted) return new ApiError({ kind: "timeout", timeoutMs }, { cause });
    return new ApiError({ kind: "network" }, { cause });
  };

  let response: Response;
  let body: unknown;
  try {
    response = await fetch(`${env.apiUrl}${path}`, {
      method: options.method ?? "GET",
      body: options.body,
      headers: { Accept: "application/json" },
      signal,
    });
    body = await readJsonBody(response);
  } catch (error) {
    throw error instanceof ApiError ? error : toTransportError(error);
  }

  if (!response.ok) {
    throw new ApiError(toHttpErrorDetail(response, body));
  }
  return body;
}

async function readJsonBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch (cause) {
    // A non-JSON error page (e.g. from a proxy) is still reported as an HTTP error.
    if (!response.ok) return undefined;
    throw new ApiError({ kind: "invalid_response", reason: "Body is not valid JSON" }, { cause });
  }
}

/** Reads the backend's `{ error: { code, message }, request_id }` envelope, if present. */
function toHttpErrorDetail(response: Response, body: unknown): ApiErrorDetail {
  const envelope = isRecord(body) && isRecord(body.error) ? body.error : undefined;
  const requestId =
    isRecord(body) && typeof body.request_id === "string"
      ? body.request_id
      : (response.headers.get("X-Request-ID") ?? undefined);

  return {
    kind: "http",
    status: response.status,
    code: typeof envelope?.code === "string" ? envelope.code : `http_${response.status}`,
    message:
      typeof envelope?.message === "string"
        ? envelope.message
        : response.statusText || "The server returned an error.",
    requestId,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
