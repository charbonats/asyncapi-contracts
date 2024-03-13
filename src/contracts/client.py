from __future__ import annotations

import abc
from typing import Any, Generic, overload

from contracts.abc.operation import BaseOperation

from .core.event_spec import MessageToPublish
from .core.operation_spec import RequestToSend
from .core.types import ParamsT, R, T


class RawOperationError(Exception):
    """Request error."""

    def __init__(
        self, code: int, description: str, headers: dict[str, str] | None, data: bytes
    ) -> None:
        self.description = description
        self.code = code
        self.headers = headers or {}
        self.data = data


class OperationError(Exception):
    """Request error."""

    def __init__(self, raw: RawOperationError) -> None:
        self.raw = raw
        msg = f"{raw.code}: {raw.description}"
        super().__init__(msg)

    @property
    def headers(self) -> dict[str, str]:
        """Get the headers."""
        return self.raw.headers

    @property
    def code(self) -> int:
        """Get the code."""
        return self.raw.code

    @property
    def description(self) -> str:
        """Get the description."""
        return self.raw.description

    @property
    def raw_data(self) -> bytes:
        """Get the raw data."""
        return self.raw.data


class RawReply:
    """Raw reply to a request."""

    def __init__(self, data: bytes, headers: dict[str, str]) -> None:
        self.data = data
        self.headers = headers


class Reply(Generic[ParamsT, T, R]):
    """A reply to a request."""

    def __init__(
        self,
        request: RequestToSend[ParamsT, T, R],
        reply: RawReply | None,
        error: RawOperationError | None,
    ) -> None:
        if reply is None and error is None:
            raise ValueError("data and error cannot be both None")
        if reply is not None and error is not None:
            raise ValueError("data and error cannot be both set")
        self.request = request
        self._reply = reply
        self._error = error
        self._data: R = ...  # type: ignore[assignment]

    def _decode_data(self, data: bytes) -> R:
        """Decode the data."""
        if self._data is ...:
            self._data = self.request._spec.reply_payload.type_adapter.decode(data)
        return self._data

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
        return self._decode_data(self._reply.data)

    def error_data(self) -> R:
        """Get the error data."""
        if not self._error:
            raise ValueError("No error")
        return self._decode_data(self._error.data)

    def error_code(self) -> int:
        """Get the error code."""
        if not self._error:
            raise ValueError("No error")
        return self._error.code

    def error_description(self) -> str:
        """Get the error description."""
        if not self._error:
            raise ValueError("No error")
        return self._error.description

    def is_error(self) -> bool:
        """Check if the reply is an error."""
        return self._error is not None


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
        msg: RequestToSend[ParamsT, T, R],
        *,
        timeout: float = 1,
        raise_on_error: bool = True,
    ) -> Reply[ParamsT, T, R]: ...

    @overload
    async def send(
        self,
        msg: MessageToPublish[ParamsT, T],
        *,
        raise_on_error: bool = True,
    ) -> None: ...

    async def send(
        self,
        msg: RequestToSend[ParamsT, T, R] | MessageToPublish[ParamsT, T],
        *,
        timeout: float = 1,
        raise_on_error: bool = True,
    ) -> Reply[ParamsT, T, R] | None:
        """Send a request or an event."""
        if isinstance(msg, RequestToSend):
            data = msg._spec.payload.type_adapter.encode(msg.payload)
            try:
                reply = await self.__send_request__(
                    msg.subject, payload=data, headers=msg.headers, timeout=timeout
                )
            except RawOperationError as e:
                if raise_on_error:
                    raise OperationError(e)
                return Reply(msg, None, e)
            return Reply(msg, reply, None)
        data = msg._spec.payload.type_adapter.encode(msg.payload)
        return await self.__send_event__(msg.subject, payload=data, headers=msg.headers)

    def decode_error(
        self,
        operation: type[BaseOperation[Any, Any, Any, R]] | RequestToSend[Any, Any, R],
        exc: OperationError,
    ) -> R:
        """Decode an error."""
        spec = operation._spec  # pyright: ignore[reportGeneralTypeIssues]
        return spec.reply_payload.type_adapter.decode(exc.raw.data)
