import { readdirSync } from "node:fs";

import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import prettier from "eslint-config-prettier/flat";

/**
 * Feature-Sliced Design boundaries, enforced with eslint-plugin-import (already
 * bundled by eslint-config-next, so no extra dependency):
 *
 * 1. A layer may only import from layers below it.
 * 2. A slice may not import from sibling slices of the same layer.
 * 3. Slices are consumed through their public API (`index.ts`), never deep imports.
 */
const LAYERS = ["app", "pages", "widgets", "features", "entities", "shared"];
const SLICED_LAYERS = ["pages", "widgets", "features", "entities"];

const slicesOf = (layer) =>
  readdirSync(new URL(`./src/${layer}`, import.meta.url), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

const layerZones = LAYERS.flatMap((layer, index) => {
  const higherLayers = LAYERS.slice(0, index);
  return higherLayers.length === 0
    ? []
    : [
        {
          target: `./src/${layer}`,
          from: higherLayers.map((higher) => `./src/${higher}`),
          message: `FSD: the "${layer}" layer must not import from higher layers (${higherLayers.join(", ")}).`,
        },
      ];
});

const crossSliceZones = SLICED_LAYERS.flatMap((layer) =>
  slicesOf(layer).map((slice) => ({
    target: `./src/${layer}/${slice}`,
    from: `./src/${layer}`,
    except: [`./${slice}`],
    message: `FSD: slices in "${layer}" must not import each other; compose them in a higher layer.`,
  })),
);

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": ["error", { fixStyle: "inline-type-imports" }],
      "import/no-cycle": "error",
      "import/no-restricted-paths": ["error", { zones: [...layerZones, ...crossSliceZones] }],
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              regex: "^@/(pages|widgets|features|entities)/[^/]+/.+",
              message:
                "FSD: import slices through their public API, e.g. '@/features/upload-image'.",
            },
            {
              regex: "^@/shared/[^/]+/.+",
              message: "FSD: import shared segments through their index, e.g. '@/shared/ui'.",
            },
          ],
        },
      ],
    },
  },
  prettier,
  globalIgnores([".next/**", "out/**", "build/**", "coverage/**", "next-env.d.ts"]),
]);

export default eslintConfig;
