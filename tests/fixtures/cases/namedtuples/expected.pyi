from __future__ import annotations
from typing import NamedTuple


class Point(NamedTuple):
    x: float
    y: float


class Config(NamedTuple):
    host: str
    port: int = ...
    debug: bool = ...


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    def to_hex(self) -> str: ...
