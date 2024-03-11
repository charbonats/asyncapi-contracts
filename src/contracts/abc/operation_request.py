from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

from ..core.types import ParamsT, R, T

if TYPE_CHECKING:
    from .operation import BaseOperation

OT = TypeVar("OT", bound="BaseOperation[Any, Any, Any, Any]")


class Request(Generic[OT], metaclass=abc.ABCMeta):
    """A message received as a request."""

    @abc.abstractmethod
    def params(self: Request[BaseOperation[Any, ParamsT, Any, Any]]) -> ParamsT:
        """Get the message parameters."""
        raise NotImplementedError

    @abc.abstractmethod
    def payload(self: Request[BaseOperation[Any, Any, T, Any]]) -> T:
        """Get the message payload."""
        raise NotImplementedError

    @abc.abstractmethod
    def headers(self) -> dict[str, str]:
        """Get the message headers."""
        raise NotImplementedError

    @overload
    @abc.abstractmethod
    async def respond(
        self: Request[BaseOperation[Any, Any, Any, None]],
        *,
        headers: dict[str, str] | None = None,
    ) -> None: ...

    @overload
    @abc.abstractmethod
    async def respond(
        self: Request[BaseOperation[Any, Any, Any, R]],
        data: R,
        *,
        headers: dict[str, str] | None = None,
    ) -> None: ...

    @abc.abstractmethod
    async def respond(
        self, data: Any = None, *, headers: dict[str, str] | None = None
    ) -> None:
        """Respond to the message."""
        raise NotImplementedError

    @overload
    @abc.abstractmethod
    async def respond_error(
        self: Request[BaseOperation[Any, Any, Any, None]],
        code: int,
        description: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> None: ...

    @overload
    @abc.abstractmethod
    async def respond_error(
        self: Request[BaseOperation[Any, ParamsT, Any, R]],
        code: int,
        description: str,
        *,
        data: R,
        headers: dict[str, str] | None = None,
    ) -> None: ...

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
