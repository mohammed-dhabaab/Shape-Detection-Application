from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImageSize:
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            msg = f"Image dimensions must be positive, got {self.width}x{self.height}"
            raise ValueError(msg)

    @property
    def pixels(self) -> int:
        return self.width * self.height
