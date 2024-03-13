from __future__ import annotations

import abc
from typing import Any, Iterable, Protocol

from .abc.consumer import BaseConsumer
from .abc.operation import BaseOperation
from .application import Application


class Resource(Protocol):
    async def stop(self) -> None: ...


class Instance(metaclass=abc.ABCMeta):
    def __init__(
        self,
        app: Application,
        operations: Iterable[BaseOperation[Any, Any, Any, Any]],
        consumers: Iterable[BaseConsumer[Any, Any, Any]],
    ) -> None:
        self.app = app
        self.operations = operations
        self.consumers = consumers

    @abc.abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    async def __aenter__(self) -> Instance:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.stop()
