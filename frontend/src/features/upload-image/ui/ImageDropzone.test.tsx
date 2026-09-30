import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { pngFile } from "@/test/fixtures";

import { ImageDropzone } from "./ImageDropzone";

function dragEvent(files: File[] = []) {
  return { dataTransfer: { types: ["Files"], files, dropEffect: "none" } };
}

describe("ImageDropzone", () => {
  it("exposes an accessible, keyboard-focusable file input", async () => {
    const user = userEvent.setup();
    render(<ImageDropzone onFiles={vi.fn()} />);

    const input = screen.getByLabelText(/drag and drop an image/i);
    await user.tab();

    expect(input).toHaveFocus();
    expect(input).toHaveAttribute("type", "file");
    expect(input).toHaveAccessibleDescription(/JPEG, PNG or WebP · up to 10 MB/);
  });

  it("passes browsed files to the caller", async () => {
    const user = userEvent.setup();
    const onFiles = vi.fn();
    render(<ImageDropzone onFiles={onFiles} />);
    const file = pngFile();

    await user.upload(screen.getByLabelText(/drag and drop an image/i), file);

    expect(onFiles).toHaveBeenCalledWith([file]);
  });

  it("shows a drag-over state and accepts dropped files", () => {
    const onFiles = vi.fn();
    render(<ImageDropzone onFiles={onFiles} />);
    const zone = screen.getByText(/drag and drop an image/i).closest("[class*='border-dashed']")!;
    const file = pngFile();

    fireEvent.dragEnter(zone, dragEvent());
    expect(screen.getByText("Drop to upload")).toBeInTheDocument();
    expect(zone).toHaveAttribute("data-dragging", "true");

    fireEvent.drop(zone, dragEvent([file]));
    expect(onFiles).toHaveBeenCalledWith([file]);
    expect(zone).not.toHaveAttribute("data-dragging");
  });

  it("clears the drag state when the pointer leaves", () => {
    render(<ImageDropzone onFiles={vi.fn()} />);
    const zone = screen.getByText(/drag and drop an image/i).closest("[class*='border-dashed']")!;

    fireEvent.dragEnter(zone, dragEvent());
    fireEvent.dragLeave(zone, dragEvent());

    expect(zone).not.toHaveAttribute("data-dragging");
  });

  it("links a validation error for assistive technology", () => {
    render(
      <>
        <p id="error">Unsupported file</p>
        <ImageDropzone onFiles={vi.fn()} errorId="error" />
      </>,
    );

    const input = screen.getByLabelText(/drag and drop an image/i);
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription(/Unsupported file/);
  });
});
