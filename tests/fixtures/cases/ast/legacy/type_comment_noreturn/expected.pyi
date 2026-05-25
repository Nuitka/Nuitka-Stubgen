from __future__ import annotations
from typing import Any, Callable


def side_effect(msg: str) -> None: ...


def no_type_info(data: Any) -> Any: ...


class Widget:
    def render(self) -> str: ...

    def on_click(self, handler: Callable, context: Any) -> None: ...
