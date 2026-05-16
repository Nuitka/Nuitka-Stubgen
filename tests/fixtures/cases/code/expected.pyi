from __future__ import annotations
from typing import Any, Dict, Generic, List, Optional, TypeVar, TypedDict, Union


def add(a: int, b: int) -> int: ...


def greet(name: str) -> str: ...


def process_data(data: list[int]) -> None: ...


class Person:
    def __init__(self, name: str, age: int) -> None: ...

    def greet(self) -> str: ...

    @classmethod
    def create_anonymous(cls) -> 'Person': ...

    @staticmethod
    def get_species() -> str: ...


class UserProfile(TypedDict):
    name: str
    email: str
    age: int
    friends: List[str]
    address: Optional[str]


class Outer:
    class Inner:
        def inner_method(self) -> str: ...

    def outer_method(self) -> 'Outer.Inner': ...


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Stack(Generic[T]):
    def __init__(self) -> None: ...

    def push(self, item: T) -> None: ...

    def pop(self) -> Optional[T]: ...


class Mapping(Generic[K, V]):
    def __init__(self) -> None: ...

    def set(self, key: K, value: V) -> None: ...

    def get(self, key: K) -> Optional[V]: ...


def process_datav2(
    data: Union[List[int], tuple[str, ...], None] = ...,
    *args: Any,
    callback: callable = ...,
    **kwargs: dict[str, Any],
) -> Union[int, str, None]: ...


x: list[Union[int, str, None]] | None = ...


def get_nested_data() -> dict[str, list[tuple[int, str]]]: ...


JsonValue: Union[str, int, float, bool, None, List[Any], Dict[str, Any]]
JsonDict: Dict[str, JsonValue]
JsonList: List[JsonDict]
JsonTuple = tuple[JsonDict, ...]
JsonSet = set[JsonDict]
JsonUnion: Union[JsonDict, JsonList, JsonTuple, JsonSet]
