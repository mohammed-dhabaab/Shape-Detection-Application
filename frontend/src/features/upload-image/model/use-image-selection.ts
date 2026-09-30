"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { env } from "@/shared/config";
import type { ImageDimensions, SniffedImageType } from "@/shared/lib";

import { validateImageFile, type ImageValidationError } from "./validate-image-file";

export interface SelectedImage {
  file: File;
  /** `blob:` URL for previews. Owned (and revoked) by this hook. */
  previewUrl: string;
  dimensions: ImageDimensions;
  type: SniffedImageType;
}

export interface RejectedFile {
  fileName: string;
  error: ImageValidationError;
}

interface SelectionState {
  image: SelectedImage | null;
  rejection: RejectedFile | null;
  isValidating: boolean;
}

const INITIAL_STATE: SelectionState = { image: null, rejection: null, isValidating: false };

export interface ImageSelection extends SelectionState {
  /** Validates the first file. Resolves `true` when it replaced the current image. */
  select: (files: File[]) => Promise<boolean>;
  clear: () => void;
  dismissRejection: () => void;
}

/**
 * Owns the user's chosen image: validation, preview URL lifecycle and replacement.
 *
 * An invalid file never discards a valid current selection; the rejection is reported
 * alongside it so the user can keep working with the previous image.
 */
export function useImageSelection({
  maxBytes = env.maxUploadBytes,
}: { maxBytes?: number } = {}): ImageSelection {
  const [state, setState] = useState<SelectionState>(INITIAL_STATE);
  // Guards against out-of-order async validation when files are chosen in quick succession.
  const latestRequest = useRef(0);
  const activeUrl = useRef<string | null>(null);

  const setPreviewUrl = useCallback((url: string | null) => {
    if (activeUrl.current) URL.revokeObjectURL(activeUrl.current);
    activeUrl.current = url;
  }, []);

  // Release the preview URL when the component using the hook unmounts.
  useEffect(() => () => setPreviewUrl(null), [setPreviewUrl]);

  const select = useCallback(
    async (files: File[]): Promise<boolean> => {
      const [file] = files;
      if (!file) return false;

      const request = ++latestRequest.current;
      setState((current) => ({ ...current, isValidating: true, rejection: null }));

      const result = await validateImageFile(file, { maxBytes });
      if (request !== latestRequest.current) return false;

      if (!result.ok) {
        setState((current) => ({
          ...current,
          isValidating: false,
          rejection: { fileName: file.name, error: result.error },
        }));
        return false;
      }

      const previewUrl = URL.createObjectURL(file);
      setPreviewUrl(previewUrl);
      setState({
        image: { file, previewUrl, dimensions: result.dimensions, type: result.type },
        rejection: null,
        isValidating: false,
      });
      return true;
    },
    [maxBytes, setPreviewUrl],
  );

  const clear = useCallback(() => {
    latestRequest.current += 1;
    setPreviewUrl(null);
    setState(INITIAL_STATE);
  }, [setPreviewUrl]);

  const dismissRejection = useCallback(() => {
    setState((current) => ({ ...current, rejection: null }));
  }, []);

  return { ...state, select, clear, dismissRejection };
}
