import {
  Circle,
  Hexagon,
  Pentagon,
  RectangleHorizontal,
  Square,
  Triangle,
  type LucideIcon,
} from "lucide-react";

import { SHAPE_CLASSES, type ShapeClass } from "../model/types";

export interface ShapeMeta {
  label: string;
  pluralLabel: string;
  icon: LucideIcon;
  /**
   * Matches the box colour on the backend's annotated image
   * (backend/app/infrastructure/image_processing/opencv_image_annotator.py).
   */
  color: string;
}

export const SHAPE_META: Record<ShapeClass, ShapeMeta> = {
  circle: { label: "Circle", pluralLabel: "Circles", icon: Circle, color: "#2563eb" },
  triangle: { label: "Triangle", pluralLabel: "Triangles", icon: Triangle, color: "#16a34a" },
  square: { label: "Square", pluralLabel: "Squares", icon: Square, color: "#dc2626" },
  rectangle: {
    label: "Rectangle",
    pluralLabel: "Rectangles",
    icon: RectangleHorizontal,
    color: "#d97706",
  },
  pentagon: { label: "Pentagon", pluralLabel: "Pentagons", icon: Pentagon, color: "#9333ea" },
  hexagon: { label: "Hexagon", pluralLabel: "Hexagons", icon: Hexagon, color: "#0891b2" },
};

export function shapeCountLabel(shape: ShapeClass, count: number): string {
  const meta = SHAPE_META[shape];
  return `${count} ${(count === 1 ? meta.label : meta.pluralLabel).toLowerCase()}`;
}

/** Per-class counts in canonical shape order, skipping absent classes. */
export function orderedClassCounts(
  byClass: Partial<Record<ShapeClass, number>>,
): Array<{ shape: ShapeClass; count: number }> {
  return SHAPE_CLASSES.flatMap((shape) => {
    const count = byClass[shape] ?? 0;
    return count > 0 ? [{ shape, count }] : [];
  });
}
