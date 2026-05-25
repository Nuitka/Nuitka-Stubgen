from __future__ import annotations
from typing import Optional


def get_value(key: str, default: Optional[str]) -> Optional[str]: ...


def configure(name: str, timeout: Optional[int]) -> None: ...


class Server:
    def __init__(self, host: str, port: int, ssl: Optional[bool]) -> None: ...
