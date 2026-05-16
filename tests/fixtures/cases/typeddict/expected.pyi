from __future__ import annotations
from typing import TypedDict


class Point(TypedDict):
    x: float
    y: float


class Config(TypedDict, total=False):
    debug: bool
    name: str


class ExtendedPoint(Point):
    z: float


class Mixed(TypedDict):
    required: str
    optional: int
