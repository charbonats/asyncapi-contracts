from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from .types import E, ParamsT, R, T

if TYPE_CHECKING:
    from .operation import Operation

OT = TypeVar("OT", bound="Operation[Any, Any, Any, Any, Any]")


class Message(Generic[OT], metaclass=abc.ABCMeta):
    """A message received as a request."""

    @abc.abstractmethod
    def params(self: Message[Operation[Any, ParamsT, Any, Any, Any]]) -> ParamsT:
        """Get the message parameters."""
        raise NotImplementedError

    @abc.abstractmethod
    def payload(self: Message[Operation[Any, Any, T, Any, Any]]) -> T:
        """Get the message payload."""
        raise NotImplementedError

    @abc.abstractmethod
    def headers(self) -> dict[str, str]:
        """Get the message headers."""
        raise NotImplementedError

    @overload
    @abc.abstractmethod
    async def respond(
        self: Message[Operation[Any, Any, Any, None, Any]],
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    @overload
    @abc.abstractmethod
    async def respond(
        self: Message[Operation[Any, Any, Any, R, Any]],
        data: R,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    @abc.abstractmethod
    async def respond(
        self, data: Any = None, *, headers: dict[str, str] | None = None
    ) -> None:
        """Respond to the message."""
        raise NotImplementedError

    @overload
    @abc.abstractmethod
    async def respond_error(
        self: Message[Operation[Any, Any, Any, Any, None]],
        code: int,
        description: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    @overload
    @abc.abstractmethod
    async def respond_error(
        self: Message[Operation[Any, ParamsT, Any, Any, E]],
        code: int,
        description: str,
        *,
        data: E,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    @abc.abstractmethod
    async def respond_error(
        self,
        code: int,
        description: str,
        *,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Respond with an error to the message."""
        raise NotImplementedError
