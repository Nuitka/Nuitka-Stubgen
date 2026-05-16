from __future__ import annotations
import attr
import attrs


@attr.s(auto_attribs=True)
class OldStylePoint:
    x: float
    y: float = ...


@attr.s(auto_attribs=True, frozen=True)
class OldStyleImmutable:
    x: float
    y: float


@attrs.define
class NewStyleConfig:
    name: str
    debug: bool = ...
    items: list[int] = ...

    def reset(self) -> None: ...


@attrs.frozen
class NewStylePoint:
    x: float
    y: float
