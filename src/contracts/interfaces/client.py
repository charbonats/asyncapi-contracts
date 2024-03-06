from __future__ import annotations

import abc
from typing import Generic, overload

from ..operation import E, OperationRequest, ParamsT, R, T
from ..event import EventPublication


class OperationError(Exception):
    """Request error."""

    def __init__(
        self, code: int, description: str, headers: dict[str, str] | None, data: bytes
    ) -> None:
        self.description = description
        self.code = code
        self.headers = headers or {}
        self.data = data


class RawReply:
    """Raw reply to a request."""

    def __init__(self, data: bytes, headers: dict[str, str]) -> None:
        self.data = data
        self.headers = headers


class Reply(Generic[ParamsT, T, R, E]):
    """Reply to a request."""

    def __init__(
        self,
        request: OperationRequest[ParamsT, T, R, E],
        reply: RawReply | None,
        error: OperationError | None,
    ) -> None:
        if reply is None and error is None:
            raise ValueError("data and error cannot be both None")
        if reply is not None and error is not None:
            raise ValueError("data and error cannot be both set")
        self.request = request
        self._reply = reply
        self._error = error

    def raise_on_error(self) -> None:
        """Check if the reply is an error."""
        if self._error is not None:
            raise self._error

    def headers(self) -> dict[str, str]:
        """Get the headers."""
        if self._reply:
            return self._reply.headers
        assert self._error
        return self._error.headers

    def data(self) -> R:
        """Get the data."""
        if self._error:
            raise self._error
        assert self._reply
        return self.request.spec.response.type_adapter.decode(self._reply.data)

    def error(self) -> E:
        """Get the error."""
        if not self._error:
            raise ValueError("No error")
        return self.request.spec.error.type_adapter.decode(self._error.data)


class Client(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def __send_request__(
        self,
        subject: str,
        payload: bytes,
        headers: dict[str, str] | None = None,
        timeout: float = 1,
    ) -> RawReply:
        """Send a request."""

    @abc.abstractmethod
    async def __send_event__(
        self,
        subject: str,
        payload: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Send an event."""

    @overload
    async def send(
        self,
        msg: OperationRequest[ParamsT, T, R, E],
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 1,
    ) -> Reply[ParamsT, T, R, E]:
        ...

    @overload
    async def send(
        self,
        msg: EventPublication[ParamsT, T],
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    async def send(
        self,
        msg: OperationRequest[ParamsT, T, R, E] | EventPublication[ParamsT, T],
        headers: dict[str, str] | None = None,
        timeout: float = 1,
    ) -> Reply[ParamsT, T, R, E] | None:
        """Send a request or an event."""
        if isinstance(msg, OperationRequest):
            data = msg.spec.request.type_adapter.encode(msg.payload)
            try:
                reply = await self.__send_request__(
                    msg.subject, payload=data, headers=headers, timeout=timeout
                )
            except OperationError as e:
                return Reply(msg, None, e)
            return Reply(msg, reply, None)
        data = msg.spec.payload.type_adapter.encode(msg.payload)
        return await self.__send_event__(msg.subject, payload=data, headers=headers)
