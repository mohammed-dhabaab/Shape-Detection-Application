"use client";

import { Shapes } from "lucide-react";

import type { DetectShapesFn } from "@/features/detect-shapes";
import { env } from "@/shared/config";
import { DetectionResultsPanel } from "@/widgets/detection-results";
import { ImageInputPanel } from "@/widgets/image-input-panel";

import { useDetectionWorkflow } from "../model/use-detection-workflow";

interface DetectionPageProps {
  /** Injectable for tests; defaults to the real API client. */
  detect?: DetectShapesFn;
}

export function DetectionPage({ detect }: DetectionPageProps = {}) {
  const workflow = useDetectionWorkflow({ detect });

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <span className="flex size-9 items-center justify-center rounded-xl bg-accent text-accent-fg">
            <Shapes aria-hidden="true" className="size-5" />
          </span>
          <div>
            <p className="text-base leading-tight font-semibold text-fg">Shape Detection</p>
            <p className="text-xs text-fg-muted">Geometric shape analysis</p>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <div className="mb-8 max-w-2xl space-y-2">
          <h1 className="text-2xl font-bold tracking-tight text-balance text-fg sm:text-3xl">
            Detect geometric shapes in your images
          </h1>
          <p className="text-pretty text-fg-muted">
            Upload an image to find circles, ellipses, triangles, squares, rectangles, pentagons and
            hexagons. Each shape is located, classified and scored.
          </p>
        </div>

        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-8">
          <div className="lg:sticky lg:top-6">
            <ImageInputPanel
              selection={workflow.selection}
              onSelectFiles={workflow.selectFiles}
              onRemoveImage={workflow.removeImage}
              onDetect={workflow.startDetection}
              isProcessing={workflow.isProcessing}
              dropzoneInputRef={workflow.dropzoneInputRef}
            />
          </div>
          <DetectionResultsPanel
            state={workflow.detectionState}
            originalImageUrl={workflow.selection.image?.previewUrl ?? null}
            onAnalyzeAnother={workflow.analyzeAnother}
            onRetry={workflow.startDetection}
          />
        </div>
      </main>

      <footer className="border-t border-border text-xs text-fg-muted">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-5 sm:px-6 lg:px-8">
          <p>Classical computer-vision detection with OpenCV · Next.js &amp; FastAPI</p>
          <a
            href={`${env.apiUrl}/docs`}
            target="_blank"
            rel="noreferrer"
            className="rounded underline underline-offset-4 hover:text-fg focus-visible:ring-2 focus-visible:ring-focus focus-visible:outline-none"
          >
            API documentation
          </a>
        </div>
      </footer>
    </div>
  );
}
