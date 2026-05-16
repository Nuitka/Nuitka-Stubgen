from __future__ import annotations

from typing import NamedTuple


class Point(NamedTuple):
    x: float
    y: float


class Config(NamedTuple):
    host: str
    port: int = 8080
    debug: bool = False


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
