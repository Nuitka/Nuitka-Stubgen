from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Point:
    x: float
    y: float = ...


@dataclass
class Config:
    name: str
    values: list[int] = ...
    cache: ClassVar[dict[str, int]] = ...
    debug: bool = ...

    def reset(self) -> None: ...


@dataclass(frozen=True)
class ImmutablePoint:
    x: float
    y: float


@dataclass
class Child(Point):
    z: float = ...
