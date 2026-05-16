from typing import Any


def func_varargs(*args: int) -> None:
    pass


def func_kwargs(**kwargs: str) -> None:
    pass


def func_kwonly(*, name: str, value: int = 0) -> None:
    pass


def func_posonly(x: int, /, y: str) -> None:
    pass


def func_mixed(pos: int, /, normal: str, *args: float, kw: bool, **kwargs: Any) -> None:
    pass


def func_with_defaults(a: int, b: str = "hello", c: float = 1.0) -> None:
    pass
