from __future__ import annotations
import abc
from dataclasses import dataclass

from typing import Any, Callable, Generic, Protocol, TypeVar, cast

from .address import Address, new_address
from .types import S, ParamsT, T
from .parameters import ParametersFactory
from .schema import Schema

ET = TypeVar("ET", bound="BaseEvent[Any, Any, Any]")


class ConsumerProtocol(Generic[ParamsT, T], Protocol):
    def handle(self, request: Event[BaseEvent[S, ParamsT, T]]) -> None:
        ...


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
        self.address = cast(Address[ParamsT], new_address(address, parameters))  # type: ignore
        self.name = name
        self.parameters = parameters
        self.payload = payload
        self.metadata = metadata or {}


@dataclass
class EventPublication(Generic[ParamsT, T]):
    subject: str
    params: ParamsT
    payload: T
    spec: EventSpec[Any, ParamsT, T]


class BaseEvent(Generic[S, ParamsT, T]):
    _spec: EventSpec[S, ParamsT, T]

    def __init_subclass__(cls, spec: EventSpec[S, ParamsT, T] | None = None) -> None:
        super().__init_subclass__()
        if not hasattr(cls, "_spec") and spec is None:
            raise TypeError("Missing spec")
        if not spec:
            return
        cls._spec = spec

    @classmethod
    def publish(
        cls, data: T, *args: S.args, **kwargs: S.kwargs
    ) -> EventPublication[ParamsT, T]:
        spec = cls._spec  # type: ignore
        params = spec.parameters(*args, **kwargs)
        return EventPublication(
            subject=spec.address.get_subject(params),
            params=params,
            payload=data,
            spec=spec,
        )


class Event(Generic[ET]):
    """An event received as a request."""

    @abc.abstractmethod
    def params(self: Event[BaseEvent[S, ParamsT, T]]) -> ParamsT:
        """Get the event parameters."""
        raise NotImplementedError

    @abc.abstractmethod
    def payload(self: Event[BaseEvent[S, ParamsT, T]]) -> T:
        """Get the event payload."""
        raise NotImplementedError

    @abc.abstractmethod
    def headers(self) -> dict[str, str]:
        """Get the event headers."""
        raise NotImplementedError

    async def ack(self) -> None:
        """Acknowledge the event."""
        raise NotImplementedError

    async def nack(self, delay: float | None = None) -> None:
        """Not acknowledge the event."""
        raise NotImplementedError

    async def term(self) -> None:
        """Terminate the event."""
        raise NotImplementedError


class EventConsumer(Generic[S, ParamsT, T], metaclass=abc.ABCMeta):
    _spec: EventSpec[S, ParamsT, T]

    def __init_subclass__(cls, spec: EventSpec[S, ParamsT, T] | None = None) -> None:
        super().__init_subclass__()
        if not hasattr(cls, "_spec") and spec is None:
            raise TypeError("Missing spec")
        if not spec:
            return
        cls._spec = spec

    @property
    def event_spec(self) -> EventSpec[S, ParamsT, T]:
        return self._spec

    @abc.abstractmethod
    async def handle(self, event: Event[BaseEvent[S, ParamsT, T]]) -> None:
        raise NotImplementedError


def event(
    address: str,
    parameters: ParametersFactory[S, ParamsT],
    payload_schema: Schema[T] | type[T],
) -> Callable[[type[Any]], type[BaseEvent[S, ParamsT, T]]]:
    def wrapper(cls: type[T]) -> type[T]:
        return cls

    return wrapper  # type: ignore


def consumer(
    source: type[BaseEvent[S, ParamsT, T]],
) -> Callable[[type[Any]], type[EventConsumer[S, ParamsT, T]]]:
    def wrapper(cls: type[T]) -> type[T]:
        return cls

    return wrapper  # type: ignore
