from __future__ import annotations
from typing import Callable


def apply(func: Callable[[int], str], value: int) -> str: ...


def get_mapper() -> Callable[[int], int]: ...
