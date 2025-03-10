from src.Ast_Stubgen.stubgen import generate_text_stub
from pathlib import Path


def test_bubble_sort() -> None:
    file_path = Path(__file__).parent / "helper_files" / "bubble_sort.py"
    assert (
        generate_text_stub(file_path.as_posix())
        == """from __future__ import annotations
from typing import Any

def sorter(arr: Any) -> Any:
    ...

def sorterv2(arr: Any) -> Any:
    ...

"""
    )


def test_code_file() -> None:
    file_path = Path(__file__).parent / "helper_files" / "code.py"
    assert (
        generate_text_stub(file_path.as_posix())
        == """from __future__ import annotations
from typing import Any, Dict, Generic, List, Optional, TypeVar, TypedDict, Union
from typing_extensions import Self, TypeAlias

def add(a: int, b: int) -> int:
    ...

def greet(name: str) -> str:
    ...

def process_data(data: list[int]) -> None:
    ...

class Person:
    def __init__(self: Self, name: str, age: int) -> None: ...
    def greet(self: Self) -> str: ...
    @classmethod
    def create_anonymous(cls, ) -> 'Person': ...
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
        def inner_method(self: Self) -> str: ...

    def outer_method(self: Self) -> 'Outer.Inner': ...

T = TypeVar('T')

K = TypeVar('K')

V = TypeVar('V')

class Stack(Generic[T]):
    def __init__(self: Self) -> None: ...
    def push(self: Self, item: T) -> None: ...
    def pop(self: Self) -> Optional[T]: ...

class Mapping(Generic[K, V]):
    def __init__(self: Self) -> None: ...
    def set(self: Self, key: K, value: V) -> None: ...
    def get(self: Self, key: K) -> Optional[V]: ...

def process_datav2(data: Union[List[int], tuple[str, ...], None]) -> Union[int, str, None]:
    ...

x: list[Union[int, str, None]] | None = None
def get_nested_data() -> dict[str, list[tuple[int, str]]]:
    ...

JsonValue: TypeAlias = Union[str, int, float, bool, None, List[Any], Dict[str, Any]]
JsonDict: TypeAlias = Dict[str, JsonValue]
JsonList: TypeAlias = List[JsonDict]
JsonTuple: TypeAlias = tuple[JsonDict, ...]
JsonSet: TypeAlias = set[JsonDict]
JsonUnion: TypeAlias = Union[JsonDict, JsonList, JsonTuple, JsonSet]
"""
    )
