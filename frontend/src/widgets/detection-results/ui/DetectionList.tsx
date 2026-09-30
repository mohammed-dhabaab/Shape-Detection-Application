import { useId } from "react";

import { DetectionItem, type Detection } from "@/entities/detection";

interface DetectionListProps {
  detections: Detection[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onPreview: (id: number | null) => void;
}

export function DetectionList({ detections, selectedId, onSelect, onPreview }: DetectionListProps) {
  const headingId = useId();
  return (
    <section aria-labelledby={headingId} className="space-y-3">
      <div className="flex items-baseline justify-between gap-2">
        <h4 id={headingId} className="text-sm font-semibold text-fg">
          Detections
        </h4>
        <p className="text-xs text-fg-muted">Select a detection to highlight it on the image</p>
      </div>
      <ol className="grid gap-3 xl:grid-cols-2">
        {detections.map((detection) => (
          <DetectionItem
            key={detection.id}
            detection={detection}
            isSelected={detection.id === selectedId}
            onSelect={onSelect}
            onPreview={onPreview}
          />
        ))}
      </ol>
    </section>
  );
}
