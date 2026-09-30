import { formatPercent } from "@/shared/lib";

import type { ScoreType } from "../model/types";

export interface ScoreTypeMeta {
  /** Lower-case phrase used after the percentage: "94% geometric similarity". */
  label: string;
  /** Title-case heading, e.g. for the summary statistic. */
  title: string;
  description: string;
}

export const SCORE_TYPE_META: Record<ScoreType, ScoreTypeMeta> = {
  geometric_similarity: {
    label: "geometric similarity",
    title: "Geometric similarity",
    description:
      "How closely the outline matches an ideal version of the shape, measured from its geometry. It is not a machine-learning confidence.",
  },
  model_confidence: {
    label: "model confidence",
    title: "Model confidence",
    description: "The detection model's confidence that this shape is present.",
  },
};

/** "94% geometric similarity" */
export function formatScore(score: number, scoreType: ScoreType): string {
  return `${formatPercent(score)} ${SCORE_TYPE_META[scoreType].label}`;
}
