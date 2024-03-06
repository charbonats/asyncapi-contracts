from __future__ import annotations
import abc
from typing import Any, AsyncContextManager, Generic, TypeVar

from ..operation import Operation
from ..application import Application

T = TypeVar("T")


class Server(Generic[T], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_application(
        self,
        app: Application,
        *endpoints: Operation[Any, Any, Any, Any, Any],
    ) -> AsyncContextManager[T]:
        """Return a new service instance with additional endpoints registered."""
        raise NotImplementedError
