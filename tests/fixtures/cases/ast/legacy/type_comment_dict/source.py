from typing import Dict, List


def lookup(data, key):
    # type: (Dict[str, int], str) -> int
    return data.get(key, 0)


def merge(a, b):
    # type: (Dict[str, List[str]], Dict[str, List[str]]) -> None
    for k, v in b.items():
        a.setdefault(k, []).extend(v)
