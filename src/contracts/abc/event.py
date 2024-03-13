from __future__ import annotations

from typing import Any, Generic, overload

from ..core.event_spec import EventSpec, MessageToPublish
from ..core.types import ParamsT, S, T


class BaseEvent(Generic[S, ParamsT, T]):
    _spec: EventSpec[S, ParamsT, T]

    def __init_subclass__(cls, spec: EventSpec[S, ParamsT, T] | None = None) -> None:
        super().__init_subclass__()
        if not hasattr(cls, "_spec") and spec is None:
            raise TypeError("Missing spec")
        if not spec:
            return
        cls._spec = spec

    @overload
    @classmethod
    def publish(
        cls: type[BaseEvent[S, None, None]],
        data: None = None,
        headers: dict[str, str] | None = None,
    ) -> MessageToPublish[None, None]: ...

    @overload
    @classmethod
    def publish(
        cls: type[BaseEvent[S, None, T]],
        data: T,
        headers: dict[str, str] | None = None,
    ) -> MessageToPublish[None, T]: ...

    @overload
    @classmethod
    def publish(
        cls: type[BaseEvent[S, ParamsT, None]],
        data: None = None,
        headers: dict[str, str] | None = None,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> MessageToPublish[ParamsT, None]: ...

    @overload
    @classmethod
    def publish(
        cls: type[BaseEvent[S, ParamsT, T]],
        data: T,
        headers: dict[str, str] | None = None,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> MessageToPublish[ParamsT, T]: ...

    @classmethod
    def publish(
        cls,
        data: Any = ...,
        headers: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> MessageToPublish[Any, Any]:
        spec = cls._spec  # type: ignore
        if data is ...:
            if spec.payload.type is not type(None):
                raise TypeError("Missing request data")
            data = None
        params = spec.parameters(*args, **kwargs)
        return MessageToPublish(
            subject=spec.address.get_subject(params),
            params=params,
            payload=data,
            headers=headers,
            spec=spec,
        )
