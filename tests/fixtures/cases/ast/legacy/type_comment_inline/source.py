x = None  # type: Optional[int]
y = 0  # type: int


def func(a, b):
    # type: (str, Optional[int]) -> str
    return a * (b or 1)
