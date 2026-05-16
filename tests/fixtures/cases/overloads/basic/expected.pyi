from __future__ import annotations
from typing import overload


@overload
def process(x: int) -> int: ...


@overload
def process(x: str) -> str: ...


class Converter:
    @overload
    def convert(self, x: int) -> int: ...

    @overload
    def convert(self, x: str) -> str: ...
