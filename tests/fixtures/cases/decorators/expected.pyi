from __future__ import annotations
from typing import Any, Generator, overload
import contextlib
import dataclasses


def traced(name: str) -> Any: ...


@overload
def parse(value: int) -> int: ...


@overload
def parse(value: str) -> str: ...


@contextlib.contextmanager
def managed() -> Generator[int, None, None]: ...


@traced("top")
def decorated_call(value: int) -> int: ...


@dataclasses.dataclass
class Model:
    name: str


class Example:
    @property
    def name(self) -> str: ...

    @contextlib.contextmanager
    def managed(self) -> Generator[int, None, None]: ...

    @traced("method")
    def decorated_method(self, value: int) -> int: ...
