import abc
class Abstract(abc.ABC):
    @abc.abstractmethod
    def run(self):
        # type: () -> None
        pass
