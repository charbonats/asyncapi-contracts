from __future__ import annotations

import abc
from typing import Generic

from ..core.event_spec import EventSpec
from ..core.types import ParamsT, S, T
from .event import BaseEvent
from .event_message import Message


class BaseConsumer(Generic[S, ParamsT, T], metaclass=abc.ABCMeta):
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
    async def handle(self, event: Message[BaseEvent[S, ParamsT, T]]) -> None:
        raise NotImplementedError
