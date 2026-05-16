# Complex nested generics from real-world search
windows = {}  # type: dict[str, list[tuple[int, str]]]
casts = []  # type: List[Callable[[int], str]]


def nested():
    def inner(x):
        # type: (int) -> int
        return x

    return inner
