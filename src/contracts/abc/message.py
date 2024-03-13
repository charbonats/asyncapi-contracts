from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ..core.types import ParamsT, S, T

if TYPE_CHECKING:
    from .event import BaseEvent


ET = TypeVar("ET", bound="BaseEvent[Any, Any, Any]")


class Message(Generic[ET], metaclass=abc.ABCMeta):
    """An message received."""

    @abc.abstractmethod
    def params(self: Message[BaseEvent[S, ParamsT, T]]) -> ParamsT:
        """Get the event parameters."""
        raise NotImplementedError

    @abc.abstractmethod
    def payload(self: Message[BaseEvent[S, ParamsT, T]]) -> T:
        """Get the event payload."""
        raise NotImplementedError

    @abc.abstractmethod
    def headers(self) -> dict[str, str]:
        """Get the event headers."""
        raise NotImplementedError

    @abc.abstractmethod
    async def ack(self) -> None:
        """Acknowledge the event."""
        raise NotImplementedError

    @abc.abstractmethod
    async def nack(self, delay: float | None = None) -> None:
        """Not acknowledge the event."""
        raise NotImplementedError

    @abc.abstractmethod
    async def term(self) -> None:
        """Terminate the event."""
        raise NotImplementedError
