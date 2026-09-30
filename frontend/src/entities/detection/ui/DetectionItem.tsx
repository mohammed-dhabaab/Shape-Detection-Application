import { cn, formatPercent } from "@/shared/lib";

import { SCORE_TYPE_META } from "../lib/score";
import { SHAPE_META } from "../lib/shape-meta";
import type { Detection } from "../model/types";

import { ShapeBadge } from "./ShapeBadge";

interface DetectionItemProps {
  detection: Detection;
  isSelected?: boolean;
  /** Toggles selection, which highlights the detection on the image. */
  onSelect?: (id: number) => void;
  /** Pointer hover preview; called with `null` when the pointer leaves. */
  onPreview?: (id: number | null) => void;
}

const COORDINATE_KEYS = ["x1", "y1", "x2", "y2"] as const;

export function DetectionItem({
  detection,
  isSelected = false,
  onSelect,
  onPreview,
}: DetectionItemProps) {
  const { id, shape, score, scoreType, bbox } = detection;
  const { label: scoreLabel } = SCORE_TYPE_META[scoreType];
  const { color, label: shapeLabel } = SHAPE_META[shape];

  return (
    <li
      onMouseEnter={() => onPreview?.(id)}
      onMouseLeave={() => onPreview?.(null)}
      className={cn(
        "rounded-xl border p-4 transition-colors duration-150",
        isSelected
          ? "border-accent bg-accent-soft"
          : "border-border bg-surface hover:bg-surface-muted",
      )}
    >
      <button
        type="button"
        onClick={() => onSelect?.(id)}
        aria-pressed={isSelected}
        aria-label={`Detection ${id}: ${shapeLabel}, ${formatPercent(score)} ${scoreLabel}. Highlight on image`}
        className="-m-1.5 flex w-[calc(100%+0.75rem)] items-start justify-between gap-3 rounded-lg p-1.5 text-left focus-visible:ring-2 focus-visible:ring-focus focus-visible:outline-none"
      >
        <span className="flex items-center gap-2.5">
          <span className="rounded-md bg-surface-muted px-1.5 py-0.5 font-mono text-xs font-semibold text-fg-muted">
            #{id}
          </span>
          <ShapeBadge shape={shape} />
        </span>
        <span className="text-right leading-tight">
          <span className="block text-lg font-semibold text-fg tabular-nums">
            {formatPercent(score)}
          </span>
          <span className="block text-xs text-fg-muted">{scoreLabel}</span>
        </span>
      </button>

      <div aria-hidden="true" className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-muted">
        <div
          className="h-full rounded-full"
          style={{ width: `${Math.round(score * 100)}%`, backgroundColor: color }}
        />
      </div>

      <p className="sr-only">Bounding box coordinates in pixels:</p>
      <dl className="mt-3 grid grid-cols-4 gap-2 font-mono text-xs">
        {COORDINATE_KEYS.map((key) => (
          <div key={key} className="rounded-md bg-surface-muted px-2 py-1">
            <dt className="text-fg-muted uppercase">{key}</dt>
            <dd className="font-semibold text-fg tabular-nums">{bbox[key]}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-2 text-xs text-fg-muted tabular-nums">
        {bbox.x2 - bbox.x1} × {bbox.y2 - bbox.y1} px
      </p>
    </li>
  );
}
