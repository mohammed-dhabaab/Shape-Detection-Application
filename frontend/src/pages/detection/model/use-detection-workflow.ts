"use client";

import { useCallback, useEffect, useRef } from "react";

import { useShapeDetection, type DetectShapesFn } from "@/features/detect-shapes";
import { useImageSelection } from "@/features/upload-image";

/**
 * Coordinates the two independent features on this page. Features can't import each
 * other (FSD), so the rules that span them live here:
 *
 * - choosing a new image discards results (and cancels any request) for the old one;
 * - "analyze another" clears everything and returns focus to the upload control.
 */
export function useDetectionWorkflow({ detect }: { detect?: DetectShapesFn } = {}) {
  const selection = useImageSelection();
  const detection = useShapeDetection(detect);
  const dropzoneInputRef = useRef<HTMLInputElement>(null);
  const focusDropzonePending = useRef(false);

  const { select, clear, image } = selection;
  const { run, reset } = detection;

  const selectFiles = useCallback(
    async (files: File[]) => {
      if (await select(files)) reset();
    },
    [select, reset],
  );

  const removeImage = useCallback(() => {
    reset();
    clear();
  }, [reset, clear]);

  const startDetection = useCallback(() => {
    if (image) void run(image.file);
  }, [image, run]);

  const analyzeAnother = useCallback(() => {
    focusDropzonePending.current = true;
    removeImage();
  }, [removeImage]);

  // The dropzone only exists once the image is cleared, so focus it after rendering.
  useEffect(() => {
    if (focusDropzonePending.current && !image) {
      focusDropzonePending.current = false;
      dropzoneInputRef.current?.focus();
    }
  }, [image]);

  return {
    selection,
    detectionState: detection.state,
    isProcessing: detection.state.status === "processing",
    dropzoneInputRef,
    selectFiles,
    removeImage,
    startDetection,
    analyzeAnother,
  };
}
