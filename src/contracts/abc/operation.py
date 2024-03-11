from __future__ import annotations

import abc
from typing import Any, Coroutine, Generic, overload

from ..core.operation_spec import OperationSpec
from ..core.types import ParamsT, R, S, T
from .operation_request import Request


class RequestToSend(Generic[ParamsT, T, R]):
    """Endpoint request."""

    def __init__(
        self,
        subject: str,
        params: ParamsT,
        payload: T,
        spec: OperationSpec[Any, ParamsT, T, R],
    ) -> None:
        self.subject = subject
        self.params = params
        self.payload = payload
        self.spec = spec


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
    ) -> RequestToSend[ParamsT, T, R]: ...

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, None, T, R]], data: T
    ) -> RequestToSend[ParamsT, T, R]: ...

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, ParamsT, None, R]],
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> RequestToSend[ParamsT, T, R]: ...

    @overload
    @classmethod
    def request(
        cls, data: T, *args: S.args, **kwargs: S.kwargs
    ) -> RequestToSend[ParamsT, T, R]: ...

    @classmethod
    def request(
        cls, data: Any = ..., *args: Any, **kwargs: Any
    ) -> RequestToSend[ParamsT, T, R]:
        spec = cls._spec  # pyright: ignore[reportGeneralTypeIssues]
        if data is ...:
            if spec.payload.type is not type(None):
                raise TypeError("Missing request data")
        params = spec.parameters(*args, **kwargs)
        subject = spec.address.get_subject(params)
        return RequestToSend(
            subject=subject,
            params=params,
            payload=data,
            spec=spec,
        )
