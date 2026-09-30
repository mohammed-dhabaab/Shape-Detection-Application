"use client";

import { ImagePlus, SearchX } from "lucide-react";
import { useEffect, useRef } from "react";

import { Button } from "@/shared/ui";

export function NoDetectionsState({ onAnalyzeAnother }: { onAnalyzeAnother: () => void }) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => headingRef.current?.focus(), []);

  return (
    <div className="flex min-h-80 flex-col items-center justify-center gap-4 px-6 py-12 text-center">
      <span className="flex size-14 items-center justify-center rounded-2xl bg-surface-muted text-fg-muted">
        <SearchX aria-hidden="true" className="size-7" />
      </span>
      <div className="max-w-sm space-y-1.5">
        <h3 ref={headingRef} tabIndex={-1} className="text-lg font-semibold text-fg outline-none">
          No shapes detected
        </h3>
        <p className="text-sm text-fg-muted">
          The image was analysed successfully, but no supported geometric shapes were found. Shapes
          work best with clear edges against a contrasting background.
        </p>
      </div>
      <Button
        variant="secondary"
        onClick={onAnalyzeAnother}
        icon={<ImagePlus aria-hidden="true" className="size-4" />}
      >
        Analyze another image
      </Button>
    </div>
  );
}
