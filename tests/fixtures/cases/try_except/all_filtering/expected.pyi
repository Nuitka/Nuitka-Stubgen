from __future__ import annotations
__all__ = ["f"]


try:
    import ujson as json
except ImportError:
    pass


def f() -> None: ...
