def complex_func(a, b, c=None):
    # type: (int, str, Optional[int]) -> bool
    return True


class Database:
    connection = None  # type: Any

    def __init__(self, host, port):
        # type: (str, int) -> None
        pass

    async def query(self, sql, params=()):
        # type: (str, tuple) -> list
        return []
