from typing import ClassVar, Dict, List, Optional


class Config:
    timeout = 30  # type: int
    name = ""  # type: str
    options = {}  # type: Dict
    cache = None  # type: Optional[Dict]
    instances = 0  # type: ClassVar[int]
    items = []  # type: List[str]

    def __init__(self, path, debug):
        # type: (str, bool) -> None
        self.path = path
        self.debug = debug
