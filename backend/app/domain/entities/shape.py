from enum import StrEnum


class ShapeType(StrEnum):
    """Geometric shape classes the system can recognise.

    Values are stable, lowercase identifiers that are safe to expose in API contracts.
    """

    CIRCLE = "circle"
    TRIANGLE = "triangle"
    SQUARE = "square"
    RECTANGLE = "rectangle"
    PENTAGON = "pentagon"
    HEXAGON = "hexagon"
