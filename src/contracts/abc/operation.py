from __future__ import annotations

import abc
from typing import Any, Coroutine, Generic, overload

from ..core.operation_spec import OperationSpec, RequestToSend
from ..core.types import ParamsT, R, S, T
from .request import Request


class BaseOperation(Generic[S, ParamsT, T, R], metaclass=abc.ABCMeta):
    _spec: OperationSpec[S, ParamsT, T, R]

    def __init_subclass__(
        cls, spec: OperationSpec[S, ParamsT, T, R] | None = None
    ) -> None:
        super().__init_subclass__()
        if not hasattr(cls, "_spec") and spec is None:
            raise TypeError("Missing spec")
        if not spec:
            return
        cls._spec = spec

    @abc.abstractmethod
    def handle(
        self, request: Request[BaseOperation[S, ParamsT, T, R]]
    ) -> Coroutine[Any, Any, None]:
        raise NotImplementedError

    @property
    def spec(self) -> OperationSpec[S, ParamsT, T, R]:
        return self._spec

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, None, None, R]],
        data: None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> RequestToSend[None, None, R]: ...

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, None, T, R]],
        data: T,
        *,
        headers: dict[str, str] | None = None,
    ) -> RequestToSend[ParamsT, T, R]: ...

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, ParamsT, None, R]],
        data: None = None,
        headers: dict[str, str] | None = None,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> RequestToSend[ParamsT, T, R]: ...

    @overload
    @classmethod
    def request(
        cls,
        data: T,
        headers: dict[str, str] | None = None,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> RequestToSend[ParamsT, T, R]: ...

    @classmethod
    def request(
        cls,
        data: Any = ...,
        headers: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> RequestToSend[Any, Any, Any]:
        spec = cls._spec  # pyright: ignore[reportGeneralTypeIssues]
        if data is ...:
            if spec.payload.type is not type(None):
                raise TypeError("Missing request data")
            data = None
        params = spec.parameters(*args, **kwargs)
        subject = spec.address.get_subject(params)
        return RequestToSend(
            subject=subject,
            params=params,
            payload=data,
            headers=headers,
            spec=spec,
        )
