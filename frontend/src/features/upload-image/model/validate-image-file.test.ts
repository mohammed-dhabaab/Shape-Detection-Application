import { beforeEach, describe, expect, it, vi } from "vitest";

import { readImageDimensions } from "@/shared/lib";
import { jpegFile, pngFile, textFile } from "@/test/fixtures";

import { describeImageValidationError, validateImageFile } from "./validate-image-file";

vi.mock("@/shared/lib", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  readImageDimensions: vi.fn(),
}));

const MAX_BYTES = 1024;

describe("validateImageFile", () => {
  beforeEach(() => {
    vi.mocked(readImageDimensions).mockResolvedValue({ width: 640, height: 480 });
  });

  it("accepts a PNG and reports its type and dimensions", async () => {
    await expect(validateImageFile(pngFile(), { maxBytes: MAX_BYTES })).resolves.toEqual({
      ok: true,
      type: "image/png",
      dimensions: { width: 640, height: 480 },
    });
  });

  it("identifies JPEG content from its bytes", async () => {
    const result = await validateImageFile(jpegFile(), { maxBytes: MAX_BYTES });

    expect(result).toMatchObject({ ok: true, type: "image/jpeg" });
  });

  it("rejects empty files", async () => {
    const empty = new File([], "empty.png", { type: "image/png" });

    await expect(validateImageFile(empty, { maxBytes: MAX_BYTES })).resolves.toEqual({
      ok: false,
      error: { code: "empty" },
    });
  });

  it("rejects files over the size limit before reading them", async () => {
    const big = pngFile("big.png", 2048);

    const result = await validateImageFile(big, { maxBytes: MAX_BYTES });

    expect(result).toEqual({
      ok: false,
      error: { code: "too_large", sizeBytes: big.size, maxBytes: MAX_BYTES },
    });
    expect(readImageDimensions).not.toHaveBeenCalled();
  });

  it("rejects non-image content even with an image extension and MIME type", async () => {
    await expect(validateImageFile(textFile(), { maxBytes: MAX_BYTES })).resolves.toEqual({
      ok: false,
      error: { code: "unsupported_type" },
    });
  });

  it("rejects images the browser cannot decode", async () => {
    vi.mocked(readImageDimensions).mockRejectedValue(new Error("decode failed"));

    await expect(validateImageFile(pngFile(), { maxBytes: MAX_BYTES })).resolves.toEqual({
      ok: false,
      error: { code: "unreadable" },
    });
  });
});

describe("describeImageValidationError", () => {
  it("explains size limits with human-readable units", () => {
    expect(
      describeImageValidationError({
        code: "too_large",
        sizeBytes: 12 * 1024 * 1024,
        maxBytes: 10 * 1024 * 1024,
      }),
    ).toBe("This file is 12 MB. The maximum size is 10 MB.");
  });

  it("names the supported formats", () => {
    expect(describeImageValidationError({ code: "unsupported_type" })).toContain(
      "JPEG, PNG or WebP",
    );
  });
});
