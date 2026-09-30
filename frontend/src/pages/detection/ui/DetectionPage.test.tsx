import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DetectionResult } from "@/entities/detection";
import type { DetectShapesFn } from "@/features/detect-shapes";
import { ApiError } from "@/shared/api";
import { readImageDimensions } from "@/shared/lib";
import {
  deferred,
  detectionResult,
  emptyDetectionResult,
  pngFile,
  textFile,
} from "@/test/fixtures";

import { DetectionPage } from "./DetectionPage";

vi.mock("@/shared/lib", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  readImageDimensions: vi.fn(),
}));

function setup(detect: DetectShapesFn) {
  const user = userEvent.setup();
  render(<DetectionPage detect={detect} />);
  const upload = (file: File) =>
    user.upload(screen.getByLabelText(/drag and drop an image/i), file);
  const detectButton = () => screen.getByRole("button", { name: /detect shapes|analyzing/i });
  return { user, upload, detectButton };
}

describe("DetectionPage", () => {
  beforeEach(() => {
    vi.mocked(readImageDimensions).mockResolvedValue({ width: 800, height: 600 });
  });

  it("disables detection until an image is chosen", () => {
    const { detectButton } = setup(vi.fn());

    expect(detectButton()).toBeDisabled();
    expect(screen.getByText("Results will appear here")).toBeInTheDocument();
  });

  it("previews the image, shows progress, then renders results", async () => {
    const request = deferred<DetectionResult>();
    const detect = vi.fn<DetectShapesFn>(() => request.promise);
    const { user, upload, detectButton } = setup(detect);

    await upload(pngFile("scene.png"));
    expect(await screen.findByAltText("Preview of scene.png")).toBeInTheDocument();
    expect(screen.getByText("800 × 600 px")).toBeInTheDocument();

    await user.click(detectButton());
    expect(detectButton()).toBeDisabled();
    expect(detectButton()).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("status")).toHaveTextContent(/analyzing image/i);
    expect(detect).toHaveBeenCalledWith(expect.any(File), expect.anything());

    request.resolve(detectionResult());

    const heading = await screen.findByRole("heading", { name: "2 shapes detected" });
    await waitFor(() => expect(heading).toHaveFocus());
    expect(screen.getByRole("status")).toHaveTextContent("Analysis complete. 2 shapes detected.");
    expect(screen.getByAltText(/annotated image with 2 detected shapes/i)).toBeInTheDocument();

    const detections = screen.getByRole("region", { name: "Detections" });
    expect(within(detections).getAllByRole("listitem")).toHaveLength(2);
    const circle = within(detections).getByRole("button", {
      name: /detection 1: circle, 94% geometric similarity/i,
    });
    expect(circle).toHaveAttribute("aria-pressed", "false");
    await user.click(circle);
    expect(circle).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/highlighting #1 circle/i)).toBeInTheDocument();
    // The highlight follows the traced outline rather than the box.
    const highlight = document.querySelector("figure svg polygon[stroke]");
    expect(highlight).toHaveAttribute("points", "270,80 419,230 270,379 120,230");

    expect(screen.getByText("Avg. geometric similarity")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("shows a dedicated state when no shapes are found", async () => {
    const { user, upload, detectButton } = setup(vi.fn(async () => emptyDetectionResult()));

    await upload(pngFile());
    await user.click(detectButton());

    expect(await screen.findByRole("heading", { name: "No shapes detected" })).toBeInTheDocument();
    expect(screen.getByText(/analysed successfully/i)).toBeInTheDocument();
  });

  it("reports failures and lets the user retry", async () => {
    const detect = vi
      .fn<DetectShapesFn>()
      .mockRejectedValueOnce(new ApiError({ kind: "network" }))
      .mockResolvedValueOnce(detectionResult());
    const { user, upload, detectButton } = setup(detect);

    await upload(pngFile());
    await user.click(detectButton());

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Can't reach the detection service");
    await waitFor(() => expect(alert).toHaveFocus());

    await user.click(within(alert).getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { name: "2 shapes detected" })).toBeInTheDocument();
    expect(detect).toHaveBeenCalledTimes(2);
  });

  it("shows server-provided messages for rejected images", async () => {
    const detect = vi.fn<DetectShapesFn>().mockRejectedValue(
      new ApiError({
        kind: "http",
        status: 400,
        code: "invalid_image",
        message: "The file appears to be corrupted or is not a valid image.",
        requestId: "req-42",
      }),
    );
    const { user, upload, detectButton } = setup(detect);

    await upload(pngFile());
    await user.click(detectButton());

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The image couldn't be read");
    expect(alert).toHaveTextContent("corrupted");
    expect(alert).toHaveTextContent("Reference: req-42");
    expect(within(alert).queryByRole("button", { name: "Try again" })).not.toBeInTheDocument();
  });

  it("rejects invalid files before uploading", async () => {
    const detect = vi.fn<DetectShapesFn>();
    const { upload, detectButton } = setup(detect);

    await upload(textFile("fake.png"));

    expect(await screen.findByRole("alert")).toHaveTextContent(/“fake\.png” can't be used/);
    expect(detectButton()).toBeDisabled();
    expect(detect).not.toHaveBeenCalled();
  });

  it("resets everything and refocuses the upload control for another image", async () => {
    const { user, upload, detectButton } = setup(vi.fn(async () => detectionResult()));

    await upload(pngFile());
    await user.click(detectButton());
    await user.click(await screen.findByRole("button", { name: "Analyze another image" }));

    expect(screen.getByText("Results will appear here")).toBeInTheDocument();
    expect(screen.queryByAltText(/preview of/i)).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText(/drag and drop an image/i)).toHaveFocus());
  });

  it("discards results when a different image is chosen", async () => {
    const { user, upload, detectButton } = setup(vi.fn(async () => detectionResult()));

    await upload(pngFile("first.png"));
    await user.click(detectButton());
    await screen.findByRole("heading", { name: "2 shapes detected" });

    const replaceInput = document.querySelectorAll<HTMLInputElement>('input[type="file"]')[0]!;
    await user.upload(replaceInput, pngFile("second.png"));

    expect(await screen.findByAltText("Preview of second.png")).toBeInTheDocument();
    expect(screen.getByText("Results will appear here")).toBeInTheDocument();
  });
});
