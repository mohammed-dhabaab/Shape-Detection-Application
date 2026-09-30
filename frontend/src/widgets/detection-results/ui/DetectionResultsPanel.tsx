"use client";

import { useId } from "react";

import { type DetectionState } from "@/features/detect-shapes";
import { pluralize } from "@/shared/lib";
import { Card, CardBody, CardHeader } from "@/shared/ui";

import { DetectionErrorState } from "./DetectionErrorState";
import { DetectionResultsView } from "./DetectionResultsView";
import { NoDetectionsState } from "./NoDetectionsState";
import { ProcessingState } from "./ProcessingState";
import { ResultsPlaceholder } from "./ResultsPlaceholder";

interface DetectionResultsPanelProps {
  state: DetectionState;
  /** Preview of the analysed image, for the "Original" view. */
  originalImageUrl: string | null;
  onAnalyzeAnother: () => void;
  onRetry: () => void;
}

export function DetectionResultsPanel({
  state,
  originalImageUrl,
  onAnalyzeAnother,
  onRetry,
}: DetectionResultsPanelProps) {
  const headingId = useId();

  return (
    <Card aria-labelledby={headingId} className="min-h-[28rem]">
      <CardHeader>
        <h2 id={headingId} className="text-lg font-semibold text-fg">
          Results
        </h2>
      </CardHeader>
      <CardBody>
        {/* Persistent live region: announces progress and outcomes to screen readers. */}
        <p role="status" aria-live="polite" className="sr-only">
          {announcementFor(state)}
        </p>
        <PanelContent
          state={state}
          originalImageUrl={originalImageUrl}
          onAnalyzeAnother={onAnalyzeAnother}
          onRetry={onRetry}
        />
      </CardBody>
    </Card>
  );
}

function PanelContent({
  state,
  originalImageUrl,
  onAnalyzeAnother,
  onRetry,
}: DetectionResultsPanelProps) {
  switch (state.status) {
    case "idle":
      return <ResultsPlaceholder />;
    case "processing":
      return <ProcessingState />;
    case "error":
      return (
        <DetectionErrorState
          error={state.error}
          onRetry={onRetry}
          onChooseAnother={onAnalyzeAnother}
        />
      );
    case "success":
      return state.result.detections.length === 0 ? (
        <NoDetectionsState onAnalyzeAnother={onAnalyzeAnother} />
      ) : (
        <DetectionResultsView
          result={state.result}
          originalImageUrl={originalImageUrl}
          onAnalyzeAnother={onAnalyzeAnother}
        />
      );
  }
}

function announcementFor(state: DetectionState): string {
  switch (state.status) {
    case "idle":
      return "";
    case "processing":
      return "Analyzing image. This may take a few seconds.";
    case "error":
      // The error alert itself is announced (role="alert").
      return "";
    case "success": {
      const { total } = state.result.summary;
      return total === 0
        ? "Analysis complete. No shapes detected."
        : `Analysis complete. ${pluralize(total, "shape")} detected.`;
    }
  }
}
