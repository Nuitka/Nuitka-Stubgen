from other_module import reexported_func

__all__ = ["MY_CONST", "AliasedType", "PublicClass", "public_func", "reexported_func"]

from typing import List

AliasedType = List

MY_CONST: int = 42
_private_const: str = "hidden"


def public_func(x: int) -> int:
    return x


def _private_func() -> None:
    pass


def also_hidden() -> str:
    return "not exported"


class PublicClass:
    value: int = 0

    def method(self) -> None:
        pass


class HiddenClass:
    pass
