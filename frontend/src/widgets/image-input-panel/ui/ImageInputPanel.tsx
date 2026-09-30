"use client";

import { LockKeyhole } from "lucide-react";
import { useId, type Ref } from "react";

import { DetectShapesButton } from "@/features/detect-shapes";
import {
  ImageDropzone,
  SelectedImageCard,
  describeImageValidationError,
  type ImageSelection,
} from "@/features/upload-image";
import { Alert, Button, Card, CardBody, CardHeader, Spinner } from "@/shared/ui";

interface ImageInputPanelProps {
  selection: ImageSelection;
  onSelectFiles: (files: File[]) => void;
  onRemoveImage: () => void;
  onDetect: () => void;
  isProcessing: boolean;
  dropzoneInputRef?: Ref<HTMLInputElement>;
}

/** Step 1 and 2 of the workflow: choose an image, then start detection. */
export function ImageInputPanel({
  selection,
  onSelectFiles,
  onRemoveImage,
  onDetect,
  isProcessing,
  dropzoneInputRef,
}: ImageInputPanelProps) {
  const headingId = useId();
  const rejectionId = useId();
  const { image, rejection, isValidating } = selection;

  return (
    <Card aria-labelledby={headingId}>
      <CardHeader>
        <h2 id={headingId} className="text-lg font-semibold text-fg">
          Image
        </h2>
        <p className="flex items-center gap-1.5 text-xs text-fg-muted">
          <LockKeyhole aria-hidden="true" className="size-3.5" />
          Processed in memory, never stored
        </p>
      </CardHeader>

      <CardBody className="space-y-5">
        {image ? (
          <SelectedImageCard
            image={image}
            onReplace={onSelectFiles}
            onRemove={onRemoveImage}
            overlay={isProcessing ? <ProcessingOverlay /> : null}
          />
        ) : (
          <ImageDropzone
            onFiles={onSelectFiles}
            isValidating={isValidating}
            errorId={rejection ? rejectionId : undefined}
            inputRef={dropzoneInputRef}
          />
        )}

        {rejection ? (
          <Alert
            id={rejectionId}
            title={`“${rejection.fileName}” can't be used`}
            action={
              image ? (
                <Button variant="secondary" onClick={selection.dismissRejection}>
                  Keep current image
                </Button>
              ) : null
            }
          >
            {describeImageValidationError(rejection.error)}
          </Alert>
        ) : null}

        <DetectShapesButton
          onClick={onDetect}
          isProcessing={isProcessing}
          disabled={!image || isValidating}
        />
        {!image ? (
          <p className="-mt-2 text-center text-xs text-fg-muted">
            Choose an image to enable detection.
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}

function ProcessingOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-canvas/70 backdrop-blur-[2px]">
      <span className="flex items-center gap-2 rounded-full bg-surface px-4 py-2 text-sm font-medium text-fg shadow-md">
        <Spinner className="size-4 text-accent" />
        Analyzing…
      </span>
    </div>
  );
}
