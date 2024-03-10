from __future__ import annotations
import abc
from typing import Any, AsyncContextManager, Generic, Protocol, TypeVar

from ..operation import BaseOperation
from ..event import EventConsumer
from ..application import Application

T = TypeVar("T")
OT = TypeVar("OT", covariant=True)
CT = TypeVar("CT", covariant=True)
AT = TypeVar("AT", covariant=True)


class StartedApplication(AsyncContextManager[AT], Protocol):
    async def stop(self) -> None: ...


class StartedOperation(AsyncContextManager[OT], Protocol):
    async def stop(self) -> None: ...


class StartedConsumer(AsyncContextManager[CT], Protocol):
    async def stop(self) -> None: ...


class Server(Generic[T, OT, CT], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_application(
        self,
        app: Application,
        *components: BaseOperation[Any, Any, Any, Any, Any]
        | EventConsumer[Any, Any, Any],
    ) -> StartedApplication[T]:
        """Return a new service instance with additional endpoints registered."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add_operation(
        self, app: T, operation: BaseOperation[Any, Any, Any, Any, Any]
    ) -> StartedOperation[OT]:
        """Register a new operation with the server."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add_consumer(
        self, app: T, consumer: EventConsumer[Any, Any, Any]
    ) -> StartedConsumer[CT]:
        """Register a new consumer with the server."""
        raise NotImplementedError
