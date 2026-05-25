from typing import Union


def process(value):
    # type: (Union[int, str, bytes]) -> str
    return str(value)


def handle(value):
    # type: (Union[int, str]) -> None
    pass
