const BYTE_UNITS = ["B", "KB", "MB", "GB"] as const;

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "–";
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < BYTE_UNITS.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  const digits = unitIndex === 0 || value >= 10 ? 0 : 1;
  return `${value.toFixed(digits)} ${BYTE_UNITS[unitIndex]}`;
}

/** Formats a ratio in `[0, 1]` as a whole-number percentage, e.g. `0.936 → "94%"`. */
export function formatPercent(ratio: number): string {
  const clamped = Math.min(Math.max(ratio, 0), 1);
  return `${Math.round(clamped * 100)}%`;
}

export function formatDimensions(width: number, height: number): string {
  return `${width} × ${height} px`;
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`;
}
