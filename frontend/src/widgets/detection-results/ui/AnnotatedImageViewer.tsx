"use client";

import { useId, useState } from "react";

import {
  SHAPE_META,
  orderedClassCounts,
  shapeCountLabel,
  type DetectionResult,
} from "@/entities/detection";
import { cn, pluralize } from "@/shared/lib";

type ImageView = "annotated" | "original";

interface AnnotatedImageViewerProps {
  result: DetectionResult;
  originalImageUrl: string | null;
  /** Detection to spotlight on the image, if any. */
  activeId: number | null;
}

/** Tallest the image may render, relative to the viewport. */
const MAX_HEIGHT_VH = 65;

export function AnnotatedImageViewer({
  result,
  originalImageUrl,
  activeId,
}: AnnotatedImageViewerProps) {
  const [view, setView] = useState<ImageView>("annotated");
  const maskId = useId();
  const { width, height } = result.image;
  const active = result.detections.find((detection) => detection.id === activeId) ?? null;
  const showingOriginal = view === "original" && originalImageUrl !== null;

  const summaryText = orderedClassCounts(result.summary.byClass)
    .map(({ shape, count }) => shapeCountLabel(shape, count))
    .join(", ");

  return (
    <figure className="space-y-3">
      {originalImageUrl ? (
        <div
          role="group"
          aria-label="Image view"
          className="inline-flex rounded-lg bg-surface-muted p-1 text-sm"
        >
          {(["annotated", "original"] as const).map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={view === option}
              onClick={() => setView(option)}
              className={cn(
                "rounded-md px-3 py-1.5 font-medium capitalize transition-colors focus-visible:ring-2 focus-visible:ring-focus focus-visible:outline-none",
                view === option ? "bg-surface text-fg shadow-xs" : "text-fg-muted hover:text-fg",
              )}
            >
              {option}
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex justify-center overflow-hidden rounded-xl border border-border bg-checkerboard">
        {/* Sized from the image's own aspect ratio so nothing shifts while it loads,
            and so the SVG overlay's coordinate space matches the pixels exactly. */}
        <div
          className="relative"
          style={{
            aspectRatio: `${width} / ${height}`,
            width: `min(100%, calc(${MAX_HEIGHT_VH}vh * ${width / height}))`,
          }}
        >
          {/* data:/blob: URLs gain nothing from next/image optimisation. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={showingOriginal ? originalImageUrl : result.annotatedImageUrl}
            alt={
              showingOriginal
                ? "Original uploaded image"
                : `Annotated image with ${pluralize(result.summary.total, "detected shape")}: ${summaryText}. Each shape is outlined and labelled with its number, class and score.`
            }
            width={width}
            height={height}
            className="absolute inset-0 size-full"
          />
          {active ? (
            <svg
              aria-hidden="true"
              viewBox={`0 0 ${width} ${height}`}
              preserveAspectRatio="none"
              className="pointer-events-none absolute inset-0 size-full"
            >
              <defs>
                <mask id={maskId}>
                  <rect width={width} height={height} fill="white" />
                  <rect
                    x={active.bbox.x1}
                    y={active.bbox.y1}
                    width={active.bbox.x2 - active.bbox.x1}
                    height={active.bbox.y2 - active.bbox.y1}
                    fill="black"
                  />
                </mask>
              </defs>
              <rect
                width={width}
                height={height}
                fill="black"
                opacity={0.45}
                mask={`url(#${maskId})`}
              />
              <rect
                x={active.bbox.x1}
                y={active.bbox.y1}
                width={active.bbox.x2 - active.bbox.x1}
                height={active.bbox.y2 - active.bbox.y1}
                fill="none"
                stroke={SHAPE_META[active.shape].color}
                strokeWidth={3}
                vectorEffect="non-scaling-stroke"
              />
            </svg>
          ) : null}
        </div>
      </div>
      <figcaption className="text-xs text-fg-muted">
        {result.image.width} × {result.image.height} px
        {active
          ? ` · Highlighting #${active.id} ${SHAPE_META[active.shape].label.toLowerCase()}`
          : ""}
      </figcaption>
    </figure>
  );
}
