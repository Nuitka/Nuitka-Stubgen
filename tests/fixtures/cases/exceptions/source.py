class SimpleError(Exception):
    pass


class DetailedError(Exception):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.args[0]}"


class NetworkError(DetailedError):
    pass
