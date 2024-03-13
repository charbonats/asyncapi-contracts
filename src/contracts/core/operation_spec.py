from __future__ import annotations

from typing import Any, Generic, cast

from .address import Address
from .exception_formatter import ExceptionFormatter
from .schema import Schema
from .types import ParametersFactory, ParamsT, R, S, T


class OperationSpec(Generic[S, ParamsT, T, R]):
    """Endpoint specification."""

    def __init__(
        self,
        address: str,
        name: str,
        parameters: ParametersFactory[S, ParamsT],
        payload: Schema[T],
        reply_payload: Schema[R],
        catch: list[ExceptionFormatter[R]] | None = None,
        metadata: dict[str, Any] | None = None,
        status_code: int = 200,
    ) -> None:
        self.address = cast(Address[ParamsT], Address(address, parameters))  # type: ignore
        self.name = name
        self.parameters = parameters
        self.payload = payload
        self.reply_payload = reply_payload
        self.catch = catch or []
        self.metadata = metadata or {}
        self.status_code = status_code

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, OperationSpec):
            return False
        return (
            self.address == __value.address
            and self.name == __value.name
            and self.parameters == __value.parameters
            and self.payload == __value.payload
            and self.reply_payload == __value.reply_payload
            and self.catch == __value.catch
            and self.metadata == __value.metadata
            and self.status_code == __value.status_code
        )


class RequestToSend(Generic[ParamsT, T, R]):
    """Endpoint request."""

    def __init__(
        self,
        subject: str,
        params: ParamsT,
        payload: T,
        headers: dict[str, str] | None,
        spec: OperationSpec[Any, ParamsT, T, R],
    ) -> None:
        self.subject = subject
        self.params = params
        self.payload = payload
        self.headers = headers or {}
        self._spec = spec

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, RequestToSend):
            return False
        return (
            self.subject == __value.subject
            and self.params == __value.params
            and self.payload == __value.payload
            and self.headers == __value.headers
        )
