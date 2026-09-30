type ClassValue = string | false | null | undefined;

/** Joins conditional class names. Deliberately tiny; no dependency needed. */
export function cn(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(" ");
}
