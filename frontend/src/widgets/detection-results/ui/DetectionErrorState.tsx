"use client";

import { ImagePlus, RotateCcw } from "lucide-react";
import { useEffect, useRef } from "react";

import { describeDetectionError } from "@/features/detect-shapes";
import type { ApiError } from "@/shared/api";
import { Alert, Button } from "@/shared/ui";

interface DetectionErrorStateProps {
  error: ApiError;
  onRetry: () => void;
  onChooseAnother: () => void;
}

export function DetectionErrorState({ error, onRetry, onChooseAnother }: DetectionErrorStateProps) {
  const alertRef = useRef<HTMLDivElement>(null);
  const copy = describeDetectionError(error);

  // Move focus to the error so keyboard users land on it after the failed attempt.
  useEffect(() => alertRef.current?.focus(), []);

  return (
    <div className="flex min-h-80 flex-col justify-center">
      <Alert
        ref={alertRef}
        tabIndex={-1}
        title={copy.title}
        action={
          <div className="flex flex-wrap gap-2">
            {copy.retryable ? (
              <Button onClick={onRetry} icon={<RotateCcw aria-hidden="true" className="size-4" />}>
                Try again
              </Button>
            ) : null}
            <Button
              variant="secondary"
              onClick={onChooseAnother}
              icon={<ImagePlus aria-hidden="true" className="size-4" />}
            >
              Choose another image
            </Button>
          </div>
        }
      >
        <p>{copy.description}</p>
        {copy.reference ? (
          <p className="mt-1 font-mono text-xs">Reference: {copy.reference}</p>
        ) : null}
      </Alert>
    </div>
  );
}
