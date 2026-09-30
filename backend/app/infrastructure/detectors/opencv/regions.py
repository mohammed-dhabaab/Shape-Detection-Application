"""Recover shapes whose outlines cross other outlines (line drawings, Venn diagrams).

Edge contours only describe the *faces* the lines split the picture into. When two
outlines intersect, no single face is either shape: a rectangle overlapped by an ellipse
becomes "rectangle minus lens", "lens" and "ellipse minus lens". Each shape is the union
of adjacent faces separated only by a thin line, so this module proposes such unions:

1. Faces are the connected components of the non-edge pixels that don't touch the
   image border (those belong to the background).
2. Two faces are neighbours when at most ``max_gap`` pixels of line separate them.
3. Every connected group of 2..``max_group_size`` neighbouring faces is merged: its masks
   are combined and a morphological close fills the separating lines.
4. A group is only proposed if at least one member is *not* a valid shape on its own.
   Otherwise every grid of squares would also yield rectangles made of two squares.

The resulting outlines go through the normal measure → classify pipeline.
"""

import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from itertools import combinations

import cv2
import numpy as np
from cv2.typing import MatLike
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class RegionMergeConfig:
    """
    Attributes:
        max_gap: Widest line (in processing pixels) that may separate two faces of the
            same shape. ``0`` disables region merging.
        max_regions: Only the largest faces are considered, bounding the work per image.
        max_group_size: Most faces merged into one candidate shape.
    """

    max_gap: int = 12
    max_regions: int = 24
    max_group_size: int = 3


@dataclass(frozen=True, slots=True)
class _Face:
    x: int
    y: int
    width: int
    height: int
    mask: NDArray[np.uint8]  # cropped to the face's bounding box

    def expanded_overlaps(self, other: "_Face", margin: int) -> bool:
        return not (
            self.x + self.width + margin < other.x
            or other.x + other.width + margin < self.x
            or self.y + self.height + margin < other.y
            or other.y + other.height + margin < self.y
        )


def merged_region_contours(
    edges: MatLike,
    *,
    min_area: float,
    config: RegionMergeConfig,
    is_shape: Callable[[MatLike], bool],
) -> Iterator[MatLike]:
    """Yield outlines (in ``edges`` coordinates) of merged groups of adjacent faces."""
    if config.max_gap <= 0 or config.max_group_size < 2:
        return
    faces = _find_faces(edges, min_area, config.max_regions)
    if len(faces) < 2:
        return

    gaps = _neighbour_gaps(faces, config.max_gap)
    neighbours: dict[int, set[int]] = {index: set() for index in range(len(faces))}
    for first, second in gaps:
        neighbours[first].add(second)
        neighbours[second].add(first)

    face_is_shape = [_is_shape(face, is_shape) for face in faces]

    for group in _connected_groups(neighbours, config.max_group_size):
        if all(face_is_shape[index] for index in group):
            continue
        widest_gap = max(gaps[pair] for pair in combinations(sorted(group), 2) if pair in gaps)
        outline = _merge(faces, group, widest_gap)
        if outline is not None:
            yield outline


def _is_shape(face: _Face, is_shape: Callable[[MatLike], bool]) -> bool:
    outline = _outline(face.mask, face.x, face.y)
    return outline is not None and is_shape(outline)


def _find_faces(edges: MatLike, min_area: float, max_regions: int) -> list[_Face]:
    free = np.where(edges > 0, 0, 1).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(free, connectivity=4)
    height, width = labels.shape
    faces: list[tuple[int, _Face]] = []
    for label in range(1, count):
        x, y, face_width, face_height, area = (int(value) for value in stats[label])
        touches_border = x == 0 or y == 0 or x + face_width == width or y + face_height == height
        if area < min_area or touches_border:
            continue
        crop = labels[y : y + face_height, x : x + face_width]
        mask = np.where(crop == label, 1, 0).astype(np.uint8)
        faces.append((area, _Face(x, y, face_width, face_height, mask)))
    faces.sort(key=lambda item: item[0], reverse=True)
    return [face for _, face in faces[:max_regions]]


def _neighbour_gaps(faces: list[_Face], max_gap: int) -> dict[tuple[int, int], float]:
    """Line width separating each pair of neighbouring faces, keyed by ``(i, j)``, i < j."""
    gaps: dict[tuple[int, int], float] = {}
    for first, second in combinations(range(len(faces)), 2):
        a, b = faces[first], faces[second]
        if not a.expanded_overlaps(b, max_gap):
            continue
        canvas_a, canvas_b = _shared_canvas([a, b], padding=0).masks
        # Distance from every pixel to the nearest pixel of face ``a``.
        distance_to_a = cv2.distanceTransform(1 - canvas_a, cv2.DIST_L2, 3)
        gap = float(distance_to_a[canvas_b > 0].min())
        if gap <= max_gap:
            gaps[(first, second)] = gap
    return gaps


def _connected_groups(neighbours: dict[int, set[int]], max_size: int) -> Iterator[frozenset[int]]:
    """Every connected set of 2..max_size faces, each yielded once."""
    seen: set[frozenset[int]] = set()
    frontier = [frozenset(pair) for pair in _edges(neighbours)]
    while frontier:
        group = frontier.pop()
        if group in seen:
            continue
        seen.add(group)
        yield group
        if len(group) < max_size:
            for member in group:
                frontier.extend(group | {other} for other in neighbours[member] - group)


def _edges(neighbours: dict[int, set[int]]) -> Iterator[tuple[int, int]]:
    for node, others in neighbours.items():
        for other in others:
            if node < other:
                yield node, other


def _merge(faces: list[_Face], group: frozenset[int], gap: float) -> MatLike | None:
    kernel_size = 2 * math.ceil(gap) + 3
    members = [faces[index] for index in sorted(group)]
    canvas = _shared_canvas(members, padding=kernel_size)
    union = np.zeros_like(canvas.masks[0])
    for mask in canvas.masks:
        union |= mask
    # Closing with a kernel wider than the separating line fills it, fusing the faces.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    closed = cv2.morphologyEx(union, cv2.MORPH_CLOSE, kernel)
    return _outline(closed, canvas.left, canvas.top)


@dataclass(frozen=True, slots=True)
class _Canvas:
    """Face masks pasted into one shared frame whose origin is ``(left, top)``."""

    masks: list[NDArray[np.uint8]]
    left: int
    top: int


def _shared_canvas(faces: list[_Face], padding: int) -> _Canvas:
    left = min(face.x for face in faces) - padding
    top = min(face.y for face in faces) - padding
    right = max(face.x + face.width for face in faces) + padding
    bottom = max(face.y + face.height for face in faces) + padding
    masks: list[NDArray[np.uint8]] = []
    for face in faces:
        canvas = np.zeros((bottom - top, right - left), dtype=np.uint8)
        row, column = face.y - top, face.x - left
        canvas[row : row + face.height, column : column + face.width] = face.mask
        masks.append(canvas)
    return _Canvas(masks, left, top)


def _outline(mask: MatLike, offset_x: int, offset_y: int) -> MatLike | None:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    return largest + np.array([offset_x, offset_y], dtype=largest.dtype)
