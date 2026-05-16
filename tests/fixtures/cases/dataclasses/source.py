from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Point:
    x: float
    y: float = 0.0


@dataclass
class Config:
    name: str
    values: list[int] = field(default_factory=list)
    cache: ClassVar[dict[str, int]] = {}
    debug: bool = False

    def reset(self) -> None:
        self.values = []


@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float


@dataclass
class Child(Point):
    z: float = 0.0
