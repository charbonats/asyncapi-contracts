from __future__ import annotations

import abc
from typing import Any, Iterable

from .abc.consumer import BaseConsumer
from .abc.operation import BaseOperation
from .application import Application, validate_consumers, validate_operations
from .instance import Instance


class ServerAdapter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_instance(
        self,
        app: Application,
        operations: Iterable[BaseOperation[Any, Any, Any, Any]],
        consumers: Iterable[BaseConsumer[Any, Any, Any]],
    ) -> Instance:
        """Add a new instance to the server."""
        raise NotImplementedError


class Server:
    def __init__(self, adapter: ServerAdapter) -> None:
        self.adapter = adapter
        self._app: Application | None = None
        self._operations: list[BaseOperation[Any, Any, Any, Any]] | None = None
        self._consumers: list[BaseConsumer[Any, Any, Any]] | None = None
        self._instance: Instance | None = None

    @property
    def app(self) -> Application:
        if self._app is None:
            raise RuntimeError("No app is bound to the server yet")
        return self._app

    def bind(
        self,
        app: Application,
        *components: BaseOperation[Any, Any, Any, Any] | BaseConsumer[Any, Any, Any],
    ) -> Server:
        """Return a new service instance with additional endpoints registered."""
        self._app = app
        self._operations = validate_operations(app, components)
        self._consumers = validate_consumers(app, components)
        return self

    async def start(self) -> None:
        if self._app is None:
            raise RuntimeError("No app is bound to the server yet")
        if self._operations is None:
            raise RuntimeError("No operations are bound to the server yet")
        if self._consumers is None:
            raise RuntimeError("No consumers are bound to the server yet")
        instance = self.adapter.create_instance(
            self._app, self._operations, self._consumers
        )
        await instance.start()
        self._instance = instance

    async def stop(self) -> None:
        if self._instance is None:
            raise RuntimeError("No app is bound to the server yet")
        if self._instance:
            await self._instance.stop()

    async def __aenter__(self) -> Server:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.stop()
