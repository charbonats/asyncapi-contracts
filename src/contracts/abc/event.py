from __future__ import annotations

from typing import Any, Generic

from ..core.event_spec import EventSpec
from ..core.types import ParamsT, S, T


class EventToPublish(Generic[ParamsT, T]):
    def __init__(
        self,
        subject: str,
        params: ParamsT,
        payload: T,
        spec: EventSpec[Any, ParamsT, T],
    ) -> None:
        self.subject = subject
        self.params = params
        self.payload = payload
        self.spec = spec


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
    ) -> EventToPublish[ParamsT, T]:
        spec = cls._spec  # type: ignore
        params = spec.parameters(*args, **kwargs)
        return EventToPublish(
            subject=spec.address.get_subject(params),
            params=params,
            payload=data,
            spec=spec,
        )
