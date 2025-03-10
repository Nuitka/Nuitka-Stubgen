from typing import List, TypedDict, Optional, TypeVar, Generic, Dict, Union, Any

def add(a: int, b: int) -> int:
    return a + b


def greet(name: str) -> str:
    return f"Hello, {name}!"


def process_data(data: list[int]) -> None:
    for item in data:
        print(item)

class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, my name is {self.name} and I am {self.age} years old"

    @classmethod
    def create_anonymous(cls) -> "Person":
        return cls("Anonymous", 0)

    @staticmethod
    def get_species() -> str:
        return "Human"
    
class UserProfile(TypedDict):
    name: str
    email: str
    age: int
    friends: List[str]
    address: Optional[str]

class Outer:
    class Inner:
        def inner_method(self) -> str:
            return "Inner method"

    def outer_method(self) -> "Outer.Inner":
        return self.Inner()

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> Optional[T]:
        if not self.items:
            return None
        return self.items.pop()
    
class Mapping(Generic[K, V]):
    def __init__(self) -> None:
        self.mapping: Dict[K, V] = {}

    def set(self, key: K, value: V) -> None:
        self.mapping[key] = value

    def get(self, key: K) -> Optional[V]:
        return self.mapping.get(key)
    
def process_datav2(
    data: Union[List[int], tuple[str, ...], None] = None,
    *args: Any,
    callback: callable = None,
    **kwargs: dict[str, Any],
) -> Union[int, str, None]:
    pass


x: list[Union[int, str, None]] | None = None


def get_nested_data() -> dict[str, list[tuple[int, str]]]:
    pass


JsonValue = Union[str, int, float, bool, None, List[Any], Dict[str, Any]]
JsonDict = Dict[str, JsonValue]
JsonList = List[JsonDict]
JsonTuple = tuple[JsonDict, ...]
JsonSet = set[JsonDict]
JsonUnion = Union[JsonDict, JsonList, JsonTuple, JsonSet]
