import type { ComponentPropsWithRef } from "react";

import { cn } from "@/shared/lib";

export function Card({ className, ...props }: ComponentPropsWithRef<"section">) {
  return (
    <section
      className={cn("rounded-2xl border border-border bg-surface shadow-xs", className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: ComponentPropsWithRef<"div">) {
  return (
    <div
      className={cn("flex flex-wrap items-center justify-between gap-3 px-5 pt-5", className)}
      {...props}
    />
  );
}

export function CardBody({ className, ...props }: ComponentPropsWithRef<"div">) {
  return <div className={cn("p-5", className)} {...props} />;
}
