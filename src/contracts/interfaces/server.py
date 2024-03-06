from __future__ import annotations
import abc
from typing import Any, AsyncContextManager, Generic, TypeVar

from ..operation import BaseOperation
from ..event import EventConsumer
from ..application import Application

T = TypeVar("T")


class Server(Generic[T], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_application(
        self,
        app: Application,
        *components: BaseOperation[Any, Any, Any, Any, Any]
        | EventConsumer[Any, Any, Any],
    ) -> AsyncContextManager[T]:
        """Return a new service instance with additional endpoints registered."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add_operation(
        self, operation: BaseOperation[Any, Any, Any, Any, Any]
    ) -> None:
        """Register a new operation with the server."""
        raise NotImplementedError

    @abc.abstractmethod
    async def add_consumer(self, consumer: EventConsumer[Any, Any, Any]) -> None:
        """Register a new consumer with the server."""
        raise NotImplementedError
