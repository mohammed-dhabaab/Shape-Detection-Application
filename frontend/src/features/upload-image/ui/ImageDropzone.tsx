"use client";

import { ImageUp } from "lucide-react";
import { useId, type Ref } from "react";

import { env } from "@/shared/config";
import { cn, formatBytes } from "@/shared/lib";
import { FileDropzone, Spinner } from "@/shared/ui";

import { IMAGE_ACCEPT, SUPPORTED_FORMATS_LABEL } from "../model/validate-image-file";

interface ImageDropzoneProps {
  onFiles: (files: File[]) => void;
  isValidating?: boolean;
  /** Id of an element describing a validation error, linked for screen readers. */
  errorId?: string;
  disabled?: boolean;
  inputRef?: Ref<HTMLInputElement>;
}

export function ImageDropzone({
  onFiles,
  isValidating = false,
  errorId,
  disabled = false,
  inputRef,
}: ImageDropzoneProps) {
  const hintId = useId();
  const describedBy = [hintId, errorId].filter(Boolean).join(" ");

  return (
    <FileDropzone
      onFiles={onFiles}
      accept={IMAGE_ACCEPT}
      disabled={disabled || isValidating}
      invalid={Boolean(errorId)}
      describedBy={describedBy}
      inputRef={inputRef}
    >
      {({ isDragging }) => (
        <span className="flex flex-col items-center gap-3 px-6 py-12 text-center sm:py-16">
          <span
            className={cn(
              "flex size-14 items-center justify-center rounded-2xl transition-colors",
              isDragging ? "bg-accent text-accent-fg" : "bg-accent-soft text-accent",
            )}
          >
            {isValidating ? (
              <Spinner className="size-7" />
            ) : (
              <ImageUp aria-hidden="true" className="size-7" />
            )}
          </span>
          <span className="text-base font-semibold text-fg">
            {isValidating
              ? "Checking image…"
              : isDragging
                ? "Drop to upload"
                : "Drag and drop an image"}
          </span>
          <span className="text-sm text-fg-muted">
            or{" "}
            <span className="font-medium text-accent underline underline-offset-4">
              browse your files
            </span>
          </span>
          <span id={hintId} className="text-xs text-fg-muted">
            {SUPPORTED_FORMATS_LABEL} · up to {formatBytes(env.maxUploadBytes)}
          </span>
        </span>
      )}
    </FileDropzone>
  );
}
