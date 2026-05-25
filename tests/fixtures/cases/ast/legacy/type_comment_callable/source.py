from typing import Callable


def apply(func, value):
    # type: (Callable[[int], str], int) -> str
    return func(value)


def get_mapper():
    # type: () -> Callable[[int], int]
    def double(x):
        # type: (int) -> int
        return x * 2

    return double
