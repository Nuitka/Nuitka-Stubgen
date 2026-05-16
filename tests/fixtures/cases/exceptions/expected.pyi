from __future__ import annotations

class SimpleError(Exception):
    ...


class DetailedError(Exception):
    def __init__(self, message: str, code: int) -> None: ...

    def __str__(self) -> str: ...


class NetworkError(DetailedError):
    ...
