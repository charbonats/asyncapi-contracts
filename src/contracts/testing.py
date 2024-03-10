"""The testing module defines classes and functions for testing.

Use the `make_operation`, `make_message`, and `make_event` functions
to create instances of the `StubOperation`, `StubMessage`, and `StubEvent`
classes for testing.
"""

from __future__ import annotations

from types import new_class
from typing import Any, Generic
from typing_extensions import Literal

from .event import BaseEvent, Event

from .message import Message
from .operation import BaseOperation, OperationRequest
from .types import E, ParamsT, R, S, T


class NoResponseError(Exception):
    """Raised when the response is not available.

    This exception is never raised during normal operation.

    It is only used during testing to detect when the response
    has not been set by the micro handler and test attempts to
    access the response data or headers.
    """


class StubMessage(Message[BaseOperation[Any, ParamsT, T, R, E]]):
    """A message received as a request."""

    def __init__(
        self,
        request: OperationRequest[ParamsT, T, R, E],
        headers: dict[str, str] | None = None,
    ) -> None:
        self._params = request.params
        self._data = request.payload
        self._headers = headers or {}
        self._response_headers: dict[str, str] = ...  # type: ignore[reportAttributeAccessIssue]
        self._response_data: R = ...  # type: ignore[reportAttributeAccessIssue]
        self._response_error: E = ...  # type: ignore[reportAttributeAccessIssue]
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
        self._response_error = data
        self._response_error_code = code
        self._response_error_description = description

    def response_data(self) -> Any:
        """Use this method durign tests to get the response data."""
        if self._response_data is ...:
            raise NoResponseError("No response has been set")
        return self._response_data

    def response_error(self) -> Any:
        """Use this method during tests to get the response error."""
        if self._response_error is ...:
            raise NoResponseError("No response has been set")
        return self._response_error

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


class StubEvent(Event[BaseEvent[Any, ParamsT, T]]):
    """A stub event for testing."""

    def __init__(
        self,
        params: ParamsT,
        payload: T,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._params = params
        self._data = payload
        self._headers = headers or {}
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


class StubOperation(Generic[S, ParamsT, T, R, E]):
    """A stub operation for testing."""

    _operation: BaseOperation[S, ParamsT, T, R, E]

    def __init_subclass__(cls, operation: BaseOperation[S, ParamsT, T, R, E]) -> None:
        super().__init_subclass__()
        cls._operation = operation

    def __init__(
        self,
        *,
        result: R = ...,  # pyright: ignore[reportInvalidTypeVarUse]
        error: E = ...,  # pyright: ignore[reportInvalidTypeVarUse]
    ) -> None:
        if result is ... and error is ...:
            raise ValueError("Either result or error must be set")
        if result is not ... and error is not ...:
            raise ValueError("Either result or error must be set, not both")
        self._result = result
        self._error = error
        self._called_with: list[Message[BaseOperation[S, ParamsT, T, R, E]]] = []

    async def handle(
        self, request: Message[BaseOperation[S, ParamsT, T, R, E]]
    ) -> None:
        self._called_with.append(request)
        if self._result is not ...:
            await request.respond(self._result)
        else:
            await request.respond_error(500, "Internal Server Error", data=self._error)

    def called_with(self) -> list[Message[BaseOperation[S, ParamsT, T, R, E]]]:
        return self._called_with


def make_operation(
    operation: type[BaseOperation[S, ParamsT, T, R, E]],
    result: R = ...,
    error: E = ...,
) -> StubOperation[S, ParamsT, T, R, E]:
    new_cls = new_class(
        operation.__class__.__name__,
        (operation,),
    )
    new_cls = new_class(
        new_cls.__name__,
        (StubOperation,),
        kwds={"operation": operation},
    )
    return new_cls(result=result, error=error)


def make_message(
    request: OperationRequest[ParamsT, T, R, E],
    headers: dict[str, str] | None = None,
) -> StubMessage[ParamsT, T, R, E]:
    return StubMessage(request, headers)


def make_event(
    params: ParamsT,
    payload: T,
    headers: dict[str, str] | None = None,
) -> StubEvent[ParamsT, T]:
    return StubEvent(params, payload, headers)
