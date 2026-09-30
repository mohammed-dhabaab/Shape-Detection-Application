import type { ComponentPropsWithRef } from "react";

import { cn } from "@/shared/lib";

export function Badge({ className, ...props }: ComponentPropsWithRef<"span">) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-muted px-2.5 py-0.5 text-xs font-medium text-fg",
        className,
      )}
      {...props}
    />
  );
}
