import { cn } from "@/shared/lib";

import { SHAPE_META } from "../lib/shape-meta";
import type { ShapeClass } from "../model/types";

interface ShapeBadgeProps {
  shape: ShapeClass;
  className?: string;
}

/** Shape name with its icon and palette colour. The text label keeps meaning independent of colour. */
export function ShapeBadge({ shape, className }: ShapeBadgeProps) {
  const { label, icon: Icon, color } = SHAPE_META[shape];
  return (
    <span className={cn("inline-flex items-center gap-1.5 font-semibold text-fg", className)}>
      <Icon aria-hidden="true" className="size-4 shrink-0" style={{ color }} strokeWidth={2.5} />
      {label}
    </span>
  );
}
