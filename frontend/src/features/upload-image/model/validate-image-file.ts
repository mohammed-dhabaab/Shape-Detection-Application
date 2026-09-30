import {
  formatBytes,
  readImageDimensions,
  sniffImageType,
  type ImageDimensions,
  type SniffedImageType,
} from "@/shared/lib";

/** Hint for the native picker; real validation happens below and on the server. */
export const IMAGE_ACCEPT = "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp";
export const SUPPORTED_FORMATS_LABEL = "JPEG, PNG or WebP";

export type ImageValidationError =
  | { code: "empty" }
  | { code: "too_large"; sizeBytes: number; maxBytes: number }
  | { code: "unsupported_type" }
  | { code: "unreadable" };

export type ImageValidationResult =
  | { ok: true; type: SniffedImageType; dimensions: ImageDimensions }
  | { ok: false; error: ImageValidationError };

/**
 * Client-side validation for fast, specific feedback before uploading. Checks are
 * ordered from cheapest to most expensive; the format is taken from the file's bytes,
 * not its name or browser-reported MIME type.
 */
export async function validateImageFile(
  file: File,
  { maxBytes }: { maxBytes: number },
): Promise<ImageValidationResult> {
  if (file.size === 0) return { ok: false, error: { code: "empty" } };
  if (file.size > maxBytes) {
    return { ok: false, error: { code: "too_large", sizeBytes: file.size, maxBytes } };
  }

  const type = await sniffImageType(file).catch(() => null);
  if (!type) return { ok: false, error: { code: "unsupported_type" } };

  try {
    const dimensions = await readImageDimensions(file);
    return { ok: true, type, dimensions };
  } catch {
    return { ok: false, error: { code: "unreadable" } };
  }
}

export function describeImageValidationError(error: ImageValidationError): string {
  switch (error.code) {
    case "empty":
      return "This file is empty. Choose an image that contains data.";
    case "too_large":
      return `This file is ${formatBytes(error.sizeBytes)}. The maximum size is ${formatBytes(error.maxBytes)}.`;
    case "unsupported_type":
      return `This file type isn't supported. Choose a ${SUPPORTED_FORMATS_LABEL} image.`;
    case "unreadable":
      return "This image couldn't be read. The file may be corrupted.";
  }
}
