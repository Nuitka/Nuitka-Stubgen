from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = ["f"]

if TYPE_CHECKING:
    from os import PathLike


def f(p: PathLike) -> None: ...
def _private() -> None: ...
