from __future__ import annotations
from typing import Optional


def annotated(a: int, b: str) -> Optional[float]: ...


def type_comment_only(x: int, y: int) -> int: ...


class Handler:
    def method_annotated(self, value: str) -> int: ...

    def method_type_comment(self, data: bytes) -> str: ...
