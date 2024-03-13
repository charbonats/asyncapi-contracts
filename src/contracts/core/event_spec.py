from __future__ import annotations

from typing import Any, Generic, cast

from .address import Address
from .schema import Schema
from .types import ParametersFactory, ParamsT, S, T


class EventSpec(Generic[S, ParamsT, T]):
    """Event specification."""

    def __init__(
        self,
        address: str,
        name: str,
        parameters: ParametersFactory[S, ParamsT],
        payload: Schema[T],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.address = cast(Address[ParamsT], Address(address, parameters))  # type: ignore
        self.name = name
        self.parameters = parameters
        self.payload = payload
        self.metadata = metadata or {}


class MessageToPublish(Generic[ParamsT, T]):
    def __init__(
        self,
        subject: str,
        params: ParamsT,
        payload: T,
        headers: dict[str, str] | None,
        spec: EventSpec[Any, ParamsT, T],
    ) -> None:
        self.subject = subject
        self.params = params
        self.payload = payload
        self.headers = headers or {}
        self._spec = spec
