from typing import Optional


def annotated(a: int, b: str) -> Optional[float]:
    return float(a) if b else None


def type_comment_only(x, y):
    # type: (int, int) -> int
    return x + y


class Handler:
    def method_annotated(self, value: str) -> int:
        return len(value)

    def method_type_comment(self, data):
        # type: (bytes) -> str
        return data.decode()
