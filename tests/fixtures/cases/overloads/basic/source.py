from typing import Union, overload


@overload
def process(x: int) -> int: ...


@overload
def process(x: str) -> str: ...


def process(x: Union[int, str]) -> Union[int, str]:
    return x


class Converter:
    @overload
    def convert(self, x: int) -> int: ...

    @overload
    def convert(self, x: str) -> str: ...

    def convert(self, x: Union[int, str]) -> Union[int, str]:
        return x
