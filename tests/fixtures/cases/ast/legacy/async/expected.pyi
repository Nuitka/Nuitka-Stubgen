from __future__ import annotations
from typing import Any


async def async_func(x: int) -> int: ...


class AsyncContainer:
    async def method(self, x: int) -> str: ...

    @classmethod
    async def from_data(cls, data: Any) -> 'AsyncContainer': ...

    @staticmethod
    async def run_static(v: int) -> None: ...


def sync_wrapper() -> Any: ...
