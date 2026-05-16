import contextlib
import dataclasses
import typing


def traced(name: str):
    def decorator(func):
        return func

    return decorator


@typing.overload
def parse(value: int) -> int: ...


@typing.overload
def parse(value: str) -> str: ...


def parse(value: int | str) -> int | str:
    return value


@contextlib.contextmanager
def managed() -> typing.Generator[int, None, None]:
    yield 1


@traced("top")
def decorated_call(value: int) -> int:
    return value


@dataclasses.dataclass
class Model:
    name: str


class Example:
    @property
    def name(self) -> str:
        return "example"

    @contextlib.contextmanager
    def managed(self) -> typing.Generator[int, None, None]:
        yield 1

    @traced("method")
    def decorated_method(self, value: int) -> int:
        return value
