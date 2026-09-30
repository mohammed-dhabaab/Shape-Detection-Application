import type { ComponentPropsWithRef, ReactNode } from "react";

import { cn } from "@/shared/lib";

import { Spinner } from "./Spinner";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "md" | "lg";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-accent text-accent-fg shadow-sm hover:bg-accent-hover disabled:bg-accent/60",
  secondary:
    "border border-border bg-surface text-fg shadow-xs hover:bg-surface-muted disabled:text-fg-muted",
  ghost: "text-fg-muted hover:bg-surface-muted hover:text-fg disabled:text-fg-muted/60",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  md: "h-9 gap-1.5 px-3 text-sm",
  lg: "h-11 gap-2 px-5 text-base",
};

export interface ButtonProps extends ComponentPropsWithRef<"button"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Shows a spinner, disables the button and marks it busy for assistive technology. */
  isLoading?: boolean;
  icon?: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  isLoading = false,
  icon,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-lg font-medium whitespace-nowrap",
        "transition-colors duration-150 disabled:cursor-not-allowed",
        "focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2 focus-visible:ring-offset-canvas focus-visible:outline-none",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className,
      )}
      {...props}
    >
      {isLoading ? <Spinner className="size-4" /> : icon}
      {children}
    </button>
  );
}
