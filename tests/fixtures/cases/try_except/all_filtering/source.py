__all__ = ["f"]

try:
    import ujson as json
except ImportError:
    pass


def f() -> None: ...
def g() -> None: ...
