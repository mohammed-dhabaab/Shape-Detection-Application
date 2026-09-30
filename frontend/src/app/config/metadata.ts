import type { Metadata, Viewport } from "next";

export const appMetadata: Metadata = {
  title: {
    default: "Shape Detection",
    template: "%s · Shape Detection",
  },
  description:
    "Upload an image to detect and classify circles, triangles, squares, rectangles, pentagons and hexagons.",
  applicationName: "Shape Detection",
};

export const appViewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f6fa" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0e17" },
  ],
};
