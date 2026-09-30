"use client";

import { useRef } from "react";

import { Button, type ButtonProps } from "./Button";

export interface FilePickerButtonProps extends Omit<ButtonProps, "onClick"> {
  onFiles: (files: File[]) => void;
  accept?: string;
}

/** A regular button that opens the native file picker. */
export function FilePickerButton({ onFiles, accept, ...buttonProps }: FilePickerButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        tabIndex={-1}
        aria-hidden="true"
        className="sr-only"
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);
          event.target.value = "";
          if (files.length > 0) onFiles(files);
        }}
      />
      <Button {...buttonProps} onClick={() => inputRef.current?.click()} />
    </>
  );
}
