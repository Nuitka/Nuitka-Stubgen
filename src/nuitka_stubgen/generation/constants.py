"""Shared constants for stub generation."""

from __future__ import annotations

TYPING_MODULES = frozenset({"typing", "typing_extensions"})
TYPEVAR_LIKE = frozenset({"TypeVar", "ParamSpec", "TypeVarTuple"})
PRESERVED_FUNCTION_DECORATORS = frozenset({"classmethod", "staticmethod", "property"})

KNOWN_TYPING_NAMES = frozenset(
    {
        "Any",
        "Optional",
        "Union",
        "List",
        "Dict",
        "Set",
        "Tuple",
        "TypeVar",
        "Generic",
        "Callable",
        "Iterable",
        "Iterator",
        "Generator",
        "Type",
        "AnyStr",
        "cast",
        "overload",
        "FrozenSet",
        "Mapping",
        "MutableMapping",
        "Sequence",
        "MutableSequence",
        "AbstractSet",
        "MutableSet",
        "TypeAlias",
        "Literal",
        "Annotated",
        "Protocol",
        "TypedDict",
        "NamedTuple",
        "ClassVar",
        "Final",
        "Text",
        "TYPE_CHECKING",
    }
)
