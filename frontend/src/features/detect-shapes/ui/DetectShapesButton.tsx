import { ScanSearch } from "lucide-react";

import { Button } from "@/shared/ui";

interface DetectShapesButtonProps {
  onClick: () => void;
  isProcessing: boolean;
  disabled?: boolean;
}

export function DetectShapesButton({
  onClick,
  isProcessing,
  disabled = false,
}: DetectShapesButtonProps) {
  return (
    <Button
      size="lg"
      className="w-full"
      onClick={onClick}
      isLoading={isProcessing}
      disabled={disabled}
      icon={<ScanSearch aria-hidden="true" className="size-5" />}
    >
      {isProcessing ? "Analyzing image…" : "Detect shapes"}
    </Button>
  );
}
