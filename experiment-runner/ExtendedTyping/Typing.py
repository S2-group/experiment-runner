from abc import abstractmethod
from typing import runtime_checkable, Protocol


@runtime_checkable
class SupportsStr(Protocol):
    """An ABC with one abstract method __str__."""
    __slots__ = ()

    @abstractmethod
    def __str__(self) -> str:
        pass
