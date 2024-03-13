"""The testing module defines classes and functions for testing.

Use the `make_operation`, `make_message`, and `make_event` functions
to create instances of the `StubOperation`, `StubMessage`, and `StubEvent`
classes for testing.
"""

from __future__ import annotations

from types import new_class
from typing import Any, Generic

from typing_extensions import Literal

from .abc.event import BaseEvent, MessageToPublish
from .abc.message import Message
from .abc.operation import BaseOperation, RequestToSend
from .abc.request import Request
from .core.types import ParamsT, R, S, T


class NoResponseError(Exception):
    """Raised when the response is not available.

    This exception is never raised during normal operation.

    It is only used during testing to detect when the response
    has not been set by the micro handler and test attempts to
    access the response data or headers.
    """


class StubRequest(Request[BaseOperation[Any, ParamsT, T, R]]):
    """A message received as a request."""

    def __init__(
        self,
        request: RequestToSend[ParamsT, T, R],
    ) -> None:
        self._params = request.params
        self._data = request.payload
        self._headers = request.headers or {}
        self._response_headers: dict[str, str] = ...  # type: ignore[reportAttributeAccessIssue]
        self._response_data: R = ...  # type: ignore[reportAttributeAccessIssue]
        self._response_error_code: int = ...  # type: ignore[reportAttributeAccessIssue]
        self._response_error_description: str = ...  # type: ignore[reportAttributeAccessIssue]

    def params(self) -> ParamsT:
        return self._params

    def payload(self) -> T:
        return self._data

    def headers(self) -> dict[str, str]:
        return self._headers

    async def respond(
        self, data: Any = None, *, headers: dict[str, str] | None = None
    ) -> None:
        self._response_headers = headers or {}
        self._response_data = data

    async def respond_error(
        self,
        code: int,
        description: str,
        *,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._response_headers = headers or {}
        self._response_data = data
        self._response_error_code = code
        self._response_error_description = description

    def response_data(self) -> Any:
        """Use this method durign tests to get the response data."""
        if self._response_data is ...:
            raise NoResponseError("No response has been set")
        if self._response_error_code is not ...:
            raise ValueError("Response is an error")
        return self._response_data

    def response_error(self) -> Any:
        """Use this method during tests to get the response error."""
        if self._response_data is ...:
            raise NoResponseError("No response has been set")
        if self._response_error_code is ...:
            raise ValueError("Response is not an error")
        return self._response_data

    def response_error_code(self) -> int:
        """Use this method during tests to get the response error code."""
        if self._response_error_code is ...:
            raise NoResponseError("No response has been set")
        return self._response_error_code

    def response_error_description(self) -> str:
        """Use this method during tests to get the response error description."""
        if self._response_error_description is ...:
            raise NoResponseError("No response has been set")
        return self._response_error_description

    def response_headers(self) -> dict[str, str]:
        """Use this method during tests to get the response headers."""
        if self._response_headers is ...:
            raise NoResponseError("No response has been set")
        return self._response_headers


class StubMessage(Message[BaseEvent[Any, ParamsT, T]]):
    """A stub message for testing."""

    def __init__(
        self,
        message: MessageToPublish[ParamsT, T],
    ) -> None:
        self._params = message.params
        self._data = message.payload
        self._headers = message.headers or {}
        self._status: Literal["pending", "acked", "nacked", "termed"] = "pending"

    def params(self) -> ParamsT:
        return self._params

    def payload(self) -> T:
        return self._data

    def headers(self) -> dict[str, str]:
        return self._headers

    async def ack(self) -> None:
        if self._status != "pending":
            raise ValueError("Event has already been acknowledged")
        self._status = "acked"

    def acknowledged(self) -> bool:
        return self._status == "acked"

    async def nack(self, delay: float | None = None) -> None:
        if self._status != "pending":
            raise ValueError("Event has already been acknowledged")
        self._status = "nacked"

    def nacked(self) -> bool:
        return self._status == "nacked"

    async def term(self) -> None:
        if self._status != "pending":
            raise ValueError("Event has already been acknowledged")
        self._status = "termed"

    def termed(self) -> bool:
        return self._status == "termed"


class StubOperation(Generic[S, ParamsT, T, R]):
    """A stub operation for testing."""

    _operation: BaseOperation[S, ParamsT, T, R]

    def __init_subclass__(cls, operation: BaseOperation[S, ParamsT, T, R]) -> None:
        super().__init_subclass__()
        cls._operation = operation

    def __init__(
        self,
        result: R,
        *,
        error_code: int | None = None,
        error_description: str | None = None,
    ) -> None:
        if error_description is not None and error_code is None:
            raise ValueError("error_code must be set if error_description is set")
        self._result = result
        self._error_code = error_code
        self._error_description = error_description
        self._called_with: list[Request[BaseOperation[S, ParamsT, T, R]]] = []

    async def handle(self, request: Request[BaseOperation[S, ParamsT, T, R]]) -> None:
        self._called_with.append(request)
        if self._error_code is None:
            await request.respond(self._result)
        else:
            await request.respond_error(
                self._error_code, self._error_description or "", data=self._result
            )

    def called_with(self) -> list[Request[BaseOperation[S, ParamsT, T, R]]]:
        return self._called_with


def make_operation(
    operation: type[BaseOperation[S, ParamsT, T, R]],
    result: R = ...,
    error_code: int | None = None,
    error_description: str | None = None,
) -> StubOperation[S, ParamsT, T, R]:
    new_cls = new_class(
        operation.__class__.__name__,
        (operation,),
    )
    new_cls = new_class(
        new_cls.__name__,
        (StubOperation,),
        kwds={"operation": operation},
    )
    return new_cls(
        result=result, error_code=error_code, error_description=error_description
    )


def make_request(
    request: RequestToSend[ParamsT, T, R],
) -> StubRequest[ParamsT, T, R]:
    return StubRequest(request)


def make_message(
    message: MessageToPublish[ParamsT, T],
) -> StubMessage[ParamsT, T]:
    return StubMessage(message)
