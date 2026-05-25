def get_value(key, default):
    # type: (str, Optional[str]) -> Optional[str]
    return default


def configure(name, timeout):
    # type: (str, Optional[int]) -> None
    pass


class Server:
    def __init__(self, host, port, ssl):
        # type: (str, int, Optional[bool]) -> None
        self.host = host
        self.port = port
        self.ssl = ssl
