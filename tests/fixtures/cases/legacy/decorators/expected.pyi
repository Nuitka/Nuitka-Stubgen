from __future__ import annotations
import abc


class Abstract(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None: ...
