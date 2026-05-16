from __future__ import annotations

import attr
import attrs


@attr.s(auto_attribs=True)
class OldStylePoint:
    x: float
    y: float = 0.0


@attr.s(auto_attribs=True, frozen=True)
class OldStyleImmutable:
    x: float
    y: float


@attrs.define
class NewStyleConfig:
    name: str
    debug: bool = False
    items: list[int] = attrs.Factory(list)

    def reset(self) -> None:
        self.items = []


@attrs.frozen
class NewStylePoint:
    x: float
    y: float
