from typing import Iterable, Iterator


def first(items):
    # type: (Iterable[int]) -> int
    for i in items:
        return i
    raise ValueError


def count(start, end):
    # type: (int, int) -> Iterator[int]
    while start < end:
        yield start
        start += 1
