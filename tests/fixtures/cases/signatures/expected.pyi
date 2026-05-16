from __future__ import annotations
from typing import Any


def func_varargs(*args: int) -> None: ...


def func_kwargs(**kwargs: str) -> None: ...


def func_kwonly(*, name: str, value: int = ...) -> None: ...


def func_posonly(x: int, /, y: str) -> None: ...


def func_mixed(pos: int, /, normal: str, *args: float, kw: bool, **kwargs: Any) -> None: ...


def func_with_defaults(a: int, b: str = ..., c: float = ...) -> None: ...
