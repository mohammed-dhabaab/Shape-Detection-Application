"use client";

import { useId, useRef, useState, type DragEvent, type ReactNode, type Ref } from "react";

import { cn } from "@/shared/lib";

export interface FileDropzoneProps {
  /** Receives the chosen or dropped files. Validation is the caller's concern. */
  onFiles: (files: File[]) => void;
  /** Value for the native `accept` attribute (a hint for the picker, not validation). */
  accept?: string;
  disabled?: boolean;
  invalid?: boolean;
  /** Ids of elements describing the dropzone (constraints, errors). */
  describedBy?: string;
  inputRef?: Ref<HTMLInputElement>;
  /** Rendered inside the clickable label. Receives the current drag state. */
  children: (state: { isDragging: boolean }) => ReactNode;
  className?: string;
}

/**
 * Accessible file drop target built on a real `<input type="file">`.
 *
 * The native input stays in the tab order (visually hidden) and the visible area is its
 * `<label>`, so keyboard users get the platform's own behaviour (Enter/Space opens the
 * picker) and screen readers announce a standard file control.
 */
export function FileDropzone({
  onFiles,
  accept,
  disabled = false,
  invalid = false,
  describedBy,
  inputRef,
  children,
  className,
}: FileDropzoneProps) {
  const inputId = useId();
  const [isDragging, setIsDragging] = useState(false);
  // dragenter/dragleave fire for every child element; count depth to avoid flicker.
  const dragDepth = useRef(0);

  const hasFiles = (event: DragEvent) => event.dataTransfer.types.includes("Files");

  const handleDragEnter = (event: DragEvent<HTMLDivElement>) => {
    if (disabled || !hasFiles(event)) return;
    event.preventDefault();
    dragDepth.current += 1;
    setIsDragging(true);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    if (disabled || !hasFiles(event)) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    if (disabled || !hasFiles(event)) return;
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setIsDragging(false);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    dragDepth.current = 0;
    setIsDragging(false);
    if (disabled) return;
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) onFiles(files);
  };

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      data-dragging={isDragging || undefined}
      className={cn(
        "group relative rounded-2xl border-2 border-dashed transition-colors duration-150",
        "has-[input:focus-visible]:ring-2 has-[input:focus-visible]:ring-focus has-[input:focus-visible]:ring-offset-2 has-[input:focus-visible]:ring-offset-canvas",
        isDragging
          ? "border-accent bg-accent-soft"
          : invalid
            ? "border-danger/60 bg-surface"
            : "border-border-strong bg-surface hover:border-accent/70 hover:bg-surface-muted",
        disabled && "pointer-events-none opacity-60",
        className,
      )}
    >
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={accept}
        disabled={disabled}
        aria-describedby={describedBy}
        aria-invalid={invalid || undefined}
        className="peer sr-only"
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);
          // Reset so choosing the same file again still triggers onChange.
          event.target.value = "";
          if (files.length > 0) onFiles(files);
        }}
      />
      <label htmlFor={inputId} className="block cursor-pointer">
        {children({ isDragging })}
      </label>
    </div>
  );
}
