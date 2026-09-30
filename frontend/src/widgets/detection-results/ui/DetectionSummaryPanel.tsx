import { Info } from "lucide-react";
import { useId, type ReactNode } from "react";

import {
  SCORE_TYPE_META,
  SHAPE_META,
  ShapeBadge,
  orderedClassCounts,
  type DetectionSummary,
} from "@/entities/detection";
import { cn, formatPercent } from "@/shared/lib";

export function DetectionSummaryPanel({ summary }: { summary: DetectionSummary }) {
  const scoreMeta = summary.scoreType ? SCORE_TYPE_META[summary.scoreType] : null;
  const classCounts = orderedClassCounts(summary.byClass);
  const headingId = useId();

  return (
    <section aria-labelledby={headingId} className="space-y-4">
      <h4 id={headingId} className="sr-only">
        Summary
      </h4>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Statistic label="Shapes found" value={summary.total} />
        <Statistic label="Shape classes" value={summary.classes} />
        {summary.averageScore !== null && scoreMeta ? (
          <Statistic
            label={`Avg. ${scoreMeta.label}`}
            value={formatPercent(summary.averageScore)}
            className="col-span-2 sm:col-span-1"
          />
        ) : null}
      </dl>

      <div className="rounded-xl border border-border p-4">
        <h5 className="mb-3 text-xs font-medium tracking-wide text-fg-muted uppercase">By class</h5>
        <ul className="space-y-2.5">
          {classCounts.map(({ shape, count }) => (
            <li key={shape} className="flex items-center gap-3 text-sm">
              <ShapeBadge shape={shape} className="w-28 shrink-0" />
              <span
                aria-hidden="true"
                className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted"
              >
                <span
                  className="block h-full rounded-full"
                  style={{
                    width: `${(count / summary.total) * 100}%`,
                    backgroundColor: SHAPE_META[shape].color,
                  }}
                />
              </span>
              <span className="w-8 text-right font-semibold text-fg tabular-nums">{count}</span>
            </li>
          ))}
        </ul>
      </div>

      {scoreMeta ? (
        <p className="flex gap-2 text-xs text-fg-muted">
          <Info aria-hidden="true" className="mt-px size-3.5 shrink-0" />
          <span>
            <span className="font-medium text-fg">{scoreMeta.title}:</span> {scoreMeta.description}
          </span>
        </p>
      ) : null}
    </section>
  );
}

function Statistic({
  label,
  value,
  className,
}: {
  label: string;
  value: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-xl bg-surface-muted px-4 py-3", className)}>
      <dt className="text-xs font-medium text-fg-muted first-letter:uppercase">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold text-fg tabular-nums">{value}</dd>
    </div>
  );
}
