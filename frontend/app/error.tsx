"use client";

import { RotateCcw, TriangleAlert } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/shared/ui";

// Last-resort boundary for unexpected rendering errors. Expected failures (invalid
// files, API errors) are handled in the UI and never reach this boundary.
export default function ErrorBoundary({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-dvh items-center justify-center px-4">
      <div role="alert" className="max-w-md space-y-4 text-center">
        <TriangleAlert aria-hidden="true" className="mx-auto size-10 text-danger" />
        <h1 className="text-xl font-semibold text-fg">Something went wrong</h1>
        <p className="text-sm text-fg-muted">
          An unexpected error occurred while displaying this page. Your image was not stored.
        </p>
        <Button onClick={() => retry()} icon={<RotateCcw aria-hidden="true" className="size-4" />}>
          Try again
        </Button>
      </div>
    </main>
  );
}
