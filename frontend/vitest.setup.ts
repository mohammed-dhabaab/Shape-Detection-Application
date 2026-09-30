import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// jsdom implements neither object URLs nor image decoding.
let objectUrlCounter = 0;
URL.createObjectURL = vi.fn(() => `blob:mock/${++objectUrlCounter}`);
URL.revokeObjectURL = vi.fn();

afterEach(() => {
  cleanup();
});
