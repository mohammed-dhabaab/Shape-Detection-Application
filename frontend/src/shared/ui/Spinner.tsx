import { LoaderCircle } from "lucide-react";

import { cn } from "@/shared/lib";

/** Decorative indeterminate spinner. Pair it with visible or live-region text. */
export function Spinner({ className }: { className?: string }) {
  return <LoaderCircle aria-hidden="true" className={cn("motion-safe:animate-spin", className)} />;
}
