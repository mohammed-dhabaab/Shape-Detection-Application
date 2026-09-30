import { SHAPE_CLASSES, SHAPE_META } from "@/entities/detection";

export function ResultsPlaceholder() {
  return (
    <div className="flex min-h-80 flex-col items-center justify-center gap-5 rounded-xl border border-dashed border-border px-6 py-12 text-center">
      <ul aria-label="Supported shapes" className="flex flex-wrap justify-center gap-3">
        {SHAPE_CLASSES.map((shape) => {
          const { icon: Icon, label, color } = SHAPE_META[shape];
          return (
            <li
              key={shape}
              className="flex size-11 items-center justify-center rounded-xl bg-surface-muted"
              title={label}
            >
              <Icon aria-hidden="true" className="size-5" style={{ color }} strokeWidth={2.25} />
              <span className="sr-only">{label}</span>
            </li>
          );
        })}
      </ul>
      <div className="max-w-sm space-y-1.5">
        <p className="text-base font-semibold text-fg">Results will appear here</p>
        <p className="text-sm text-fg-muted">
          Upload an image and select <span className="font-medium text-fg">Detect shapes</span>.
          Circles, triangles, squares, rectangles, pentagons and hexagons are recognised.
        </p>
      </div>
    </div>
  );
}
