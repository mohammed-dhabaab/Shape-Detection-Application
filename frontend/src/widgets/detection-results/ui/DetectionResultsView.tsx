"use client";

import { ImagePlus } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { DetectionResult } from "@/entities/detection";
import { pluralize } from "@/shared/lib";
import { Button } from "@/shared/ui";

import { AnnotatedImageViewer } from "./AnnotatedImageViewer";
import { DetectionList } from "./DetectionList";
import { DetectionSummaryPanel } from "./DetectionSummaryPanel";

interface DetectionResultsViewProps {
  result: DetectionResult;
  originalImageUrl: string | null;
  onAnalyzeAnother: () => void;
}

/** Successful analysis with at least one detection. */
export function DetectionResultsView({
  result,
  originalImageUrl,
  onAnalyzeAnother,
}: DetectionResultsViewProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  // `selectedId` is sticky (click/keyboard); `previewId` follows the pointer.
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [previewId, setPreviewId] = useState<number | null>(null);
  const activeId = previewId ?? selectedId;

  // Move focus to the new content so keyboard and screen-reader users land on it.
  useEffect(() => headingRef.current?.focus(), []);

  const { total } = result.summary;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 ref={headingRef} tabIndex={-1} className="text-base font-semibold text-fg outline-none">
          {pluralize(total, "shape")} detected
        </h3>
        <Button
          variant="secondary"
          onClick={onAnalyzeAnother}
          icon={<ImagePlus aria-hidden="true" className="size-4" />}
        >
          Analyze another image
        </Button>
      </div>

      <AnnotatedImageViewer
        result={result}
        originalImageUrl={originalImageUrl}
        activeId={activeId}
      />

      <DetectionSummaryPanel summary={result.summary} />

      <DetectionList
        detections={result.detections}
        selectedId={selectedId}
        onSelect={(id) => setSelectedId((current) => (current === id ? null : id))}
        onPreview={setPreviewId}
      />
    </div>
  );
}
