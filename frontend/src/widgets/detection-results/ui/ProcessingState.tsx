import { Spinner } from "@/shared/ui";

/** Indeterminate progress: the backend reports no progress, so none is invented. */
export function ProcessingState() {
  return (
    <div aria-hidden="true" className="space-y-4">
      <div className="relative flex aspect-[4/3] items-center justify-center overflow-hidden rounded-xl bg-surface-muted">
        <div className="absolute inset-0 bg-linear-to-br from-transparent via-white/5 to-transparent motion-safe:animate-pulse" />
        <div className="flex flex-col items-center gap-3 text-sm text-fg-muted">
          <Spinner className="size-8 text-accent" />
          <span className="font-medium text-fg">Analyzing image…</span>
          <span>Finding contours and classifying shapes</span>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[0, 1, 2].map((index) => (
          <div key={index} className="h-16 rounded-xl bg-surface-muted motion-safe:animate-pulse" />
        ))}
      </div>
    </div>
  );
}
