"use client";

import { RefreshCw, X } from "lucide-react";
import type { ReactNode } from "react";

import { formatBytes, formatDimensions } from "@/shared/lib";
import { Button, FilePickerButton } from "@/shared/ui";

import type { SelectedImage } from "../model/use-image-selection";
import { IMAGE_ACCEPT } from "../model/validate-image-file";

const FORMAT_LABELS: Record<SelectedImage["type"], string> = {
  "image/jpeg": "JPEG",
  "image/png": "PNG",
  "image/webp": "WebP",
};

interface SelectedImageCardProps {
  image: SelectedImage;
  onReplace: (files: File[]) => void;
  onRemove: () => void;
  /** Rendered over the preview (e.g. a processing indicator). */
  overlay?: ReactNode;
}

export function SelectedImageCard({ image, onReplace, onRemove, overlay }: SelectedImageCardProps) {
  const { file, previewUrl, dimensions, type } = image;

  return (
    <div className="space-y-4">
      <div className="relative flex items-center justify-center overflow-hidden rounded-xl border border-border bg-checkerboard">
        {/* A blob: preview doesn't benefit from next/image optimisation. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={previewUrl}
          alt={`Preview of ${file.name}`}
          width={dimensions.width}
          height={dimensions.height}
          className="max-h-80 w-auto max-w-full object-contain"
        />
        {overlay}
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
        <MetadataItem label="File" className="col-span-2 sm:col-span-4">
          <span className="block truncate" title={file.name}>
            {file.name}
          </span>
        </MetadataItem>
        <MetadataItem label="Size">{formatBytes(file.size)}</MetadataItem>
        <MetadataItem label="Format">{FORMAT_LABELS[type]}</MetadataItem>
        <MetadataItem label="Dimensions" className="col-span-2">
          {formatDimensions(dimensions.width, dimensions.height)}
        </MetadataItem>
      </dl>

      <div className="flex flex-wrap gap-2">
        <FilePickerButton
          variant="secondary"
          accept={IMAGE_ACCEPT}
          onFiles={onReplace}
          icon={<RefreshCw aria-hidden="true" className="size-4" />}
        >
          Replace image
        </FilePickerButton>
        <Button
          variant="ghost"
          onClick={onRemove}
          icon={<X aria-hidden="true" className="size-4" />}
        >
          Remove
        </Button>
      </div>
    </div>
  );
}

function MetadataItem({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={className}>
      <dt className="text-xs font-medium tracking-wide text-fg-muted uppercase">{label}</dt>
      <dd className="font-medium text-fg tabular-nums">{children}</dd>
    </div>
  );
}
