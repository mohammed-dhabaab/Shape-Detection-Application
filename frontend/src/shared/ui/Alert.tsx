import { CircleAlert, Info } from "lucide-react";
import type { ComponentPropsWithRef, ReactNode } from "react";

import { cn } from "@/shared/lib";

type AlertTone = "error" | "info";

const TONE_CLASSES: Record<AlertTone, string> = {
  error: "border-danger/30 bg-danger-soft text-danger-strong",
  info: "border-border bg-surface-muted text-fg",
};

export interface AlertProps extends Omit<ComponentPropsWithRef<"div">, "title"> {
  tone?: AlertTone;
  title: ReactNode;
  action?: ReactNode;
}

/**
 * Inline message. Errors use `role="alert"` so they are announced immediately; the
 * icon plus title text means the tone never relies on colour alone.
 */
export function Alert({
  tone = "error",
  title,
  action,
  children,
  className,
  ...props
}: AlertProps) {
  const Icon = tone === "error" ? CircleAlert : Info;
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "flex gap-3 rounded-xl border p-4 text-sm outline-none",
        TONE_CLASSES[tone],
        className,
      )}
      {...props}
    >
      <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-semibold">{title}</p>
        {children ? <div className="text-fg-muted">{children}</div> : null}
        {action ? <div className="pt-2">{action}</div> : null}
      </div>
    </div>
  );
}
