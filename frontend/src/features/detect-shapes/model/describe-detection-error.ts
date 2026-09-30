import type { ApiError } from "@/shared/api";
import { env } from "@/shared/config";

export interface DetectionErrorCopy {
  title: string;
  description: string;
  /** Whether retrying the same image could plausibly succeed. */
  retryable: boolean;
  /** Correlates the failure with server logs, when the server provided one. */
  reference?: string;
}

/** Maps a failed request to user-facing copy. Exhaustive over every error kind. */
export function describeDetectionError(error: ApiError): DetectionErrorCopy {
  const { detail } = error;
  switch (detail.kind) {
    case "network":
      return {
        title: "Can't reach the detection service",
        description: `Check your connection and that the API is running at ${env.apiUrl}, then try again.`,
        retryable: true,
      };
    case "timeout":
      return {
        title: "The analysis took too long",
        description: "The server didn't respond in time. Try again, or use a smaller image.",
        retryable: true,
      };
    case "aborted":
      return {
        title: "Analysis cancelled",
        description: "The request was cancelled before it finished.",
        retryable: true,
      };
    case "invalid_response":
      return {
        title: "Unexpected response from the server",
        description: "The server's reply couldn't be understood. Please try again.",
        retryable: true,
      };
    case "http":
      return describeHttpError(detail.status, detail.code, detail.message, detail.requestId);
  }
}

const TITLES_BY_CODE: Record<string, string> = {
  empty_file: "The image is empty",
  file_too_large: "The image is too large",
  image_too_large: "The image dimensions are too large",
  unsupported_format: "Unsupported image format",
  invalid_image: "The image couldn't be read",
};

function describeHttpError(
  status: number,
  code: string,
  message: string,
  requestId: string | undefined,
): DetectionErrorCopy {
  if (status >= 500) {
    return {
      title: "Something went wrong on the server",
      description: "The image couldn't be analysed right now. Please try again in a moment.",
      retryable: true,
      reference: requestId,
    };
  }
  return {
    title: TITLES_BY_CODE[code] ?? "The image couldn't be analysed",
    // 4xx messages from the API are written for end users.
    description: message,
    retryable: status === 408 || status === 429,
    reference: requestId,
  };
}
