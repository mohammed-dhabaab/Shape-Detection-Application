export interface ImageDimensions {
  width: number;
  height: number;
}

export type SniffedImageType = "image/jpeg" | "image/png" | "image/webp";

const SIGNATURE_LENGTH = 12;

/**
 * Identifies JPEG, PNG or WebP from the file's leading bytes. The browser-reported
 * MIME type comes from the file extension and can't be trusted on its own.
 */
export async function sniffImageType(file: Blob): Promise<SniffedImageType | null> {
  const bytes = await readLeadingBytes(file, SIGNATURE_LENGTH);
  const startsWith = (signature: number[], offset = 0) =>
    signature.every((byte, index) => bytes[offset + index] === byte);

  if (startsWith([0xff, 0xd8, 0xff])) return "image/jpeg";
  if (startsWith([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) return "image/png";
  // "RIFF" <4-byte size> "WEBP"
  if (startsWith([0x52, 0x49, 0x46, 0x46]) && startsWith([0x57, 0x45, 0x42, 0x50], 8)) {
    return "image/webp";
  }
  return null;
}

/** Decodes the image header to read its (EXIF-oriented) pixel dimensions. */
export async function readImageDimensions(file: Blob): Promise<ImageDimensions> {
  if (typeof createImageBitmap === "function") {
    const bitmap = await createImageBitmap(file);
    try {
      return { width: bitmap.width, height: bitmap.height };
    } finally {
      bitmap.close();
    }
  }
  return readDimensionsWithImageElement(file);
}

function readDimensionsWithImageElement(file: Blob): Promise<ImageDimensions> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      resolve({ width: image.naturalWidth, height: image.naturalHeight });
      URL.revokeObjectURL(url);
    };
    image.onerror = () => {
      reject(new Error("The file could not be decoded as an image."));
      URL.revokeObjectURL(url);
    };
    image.src = url;
  });
}

async function readLeadingBytes(file: Blob, count: number): Promise<Uint8Array> {
  const slice = file.slice(0, count);
  if (typeof slice.arrayBuffer === "function") {
    return new Uint8Array(await slice.arrayBuffer());
  }
  // Fallback for environments without Blob.arrayBuffer (older engines, some test DOMs).
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer));
    reader.onerror = () => reject(reader.error ?? new Error("Could not read file."));
    reader.readAsArrayBuffer(slice);
  });
}
