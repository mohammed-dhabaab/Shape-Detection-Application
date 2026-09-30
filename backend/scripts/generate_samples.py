"""Generate demo images for manual testing and screenshots.

Usage (from ``backend/``)::

    uv run python -m scripts.generate_samples [output_dir]

Writes to ``../samples`` by default.
"""

import sys
from pathlib import Path

from tests.fixtures.synthetic_images import DARK, ShapeSpec, all_shapes_scene, encode, render

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "samples"


def build_samples() -> dict[str, bytes]:
    _, all_shapes = all_shapes_scene()
    outlined = render(
        [
            ShapeSpec("circle", (170, 170), 110, color=(40, 40, 40), thickness=6),
            ShapeSpec("hexagon", (480, 170), 110, color=(40, 40, 40), thickness=6),
            ShapeSpec("triangle", (780, 190), 120, color=(40, 40, 40), thickness=6),
            ShapeSpec("rectangle", (300, 470), 360, color=(40, 40, 40), thickness=6, aspect=0.45),
            ShapeSpec("square", (720, 470), 200, color=(40, 40, 40), thickness=6, rotation_deg=20),
        ],
        width=960,
        height=640,
    )
    night_sky = render(
        [
            ShapeSpec("circle", (160, 150), 70, color=(120, 220, 250)),
            ShapeSpec("circle", (420, 130), 45, color=(250, 220, 120)),
            ShapeSpec("pentagon", (700, 160), 90, color=(200, 150, 250), rotation_deg=12),
            ShapeSpec("triangle", (220, 440), 110, color=(140, 250, 160), rotation_deg=180),
            ShapeSpec("square", (520, 440), 170, color=(250, 250, 250), rotation_deg=35),
            ShapeSpec("hexagon", (790, 450), 95, color=(120, 180, 250)),
        ],
        width=960,
        height=640,
        background=DARK,
        noise_sigma=6,
    )
    empty = render([], width=640, height=480, background=(235, 240, 245))
    return {
        "all-shapes.png": encode(all_shapes),
        "outlined-shapes.png": encode(outlined),
        "night-sky.jpg": encode(night_sky, ".jpg"),
        "no-shapes.webp": encode(empty, ".webp"),
    }


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    for name, data in build_samples().items():
        (output / name).write_bytes(data)
        print(f"wrote {output / name} ({len(data) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
