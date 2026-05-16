from __future__ import annotations
from other_module import reexported_func as reexported_func
from typing import List

__all__ = ["AliasedType", "MY_CONST", "PublicClass", "public_func", "reexported_func"]


AliasedType: List
MY_CONST: int = ...


def public_func(x: int) -> int: ...






class PublicClass:
    value: int = ...

    def method(self) -> None: ...
