/**
 * Public runtime configuration.
 *
 * `NEXT_PUBLIC_*` variables are inlined at build time, so they must be referenced
 * literally (not via dynamic keys) for Next.js to substitute them.
 */

const DEFAULT_API_URL = "http://localhost:8000";
const DEFAULT_MAX_UPLOAD_MB = 10;
const BYTES_PER_MB = 1024 * 1024;

function parsePositiveNumber(raw: string | undefined, fallback: number): number {
  const value = Number(raw);
  return raw && Number.isFinite(value) && value > 0 ? value : fallback;
}

export const env = {
  /** Base URL of the detection API, without a trailing slash. */
  apiUrl: (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL).replace(/\/+$/, ""),
  /**
   * Client-side upload limit, used for immediate feedback. The backend enforces its
   * own limit and remains the source of truth.
   */
  maxUploadBytes:
    parsePositiveNumber(process.env.NEXT_PUBLIC_MAX_UPLOAD_MB, DEFAULT_MAX_UPLOAD_MB) *
    BYTES_PER_MB,
} as const;
