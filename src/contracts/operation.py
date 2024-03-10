from __future__ import annotations

import abc
from dataclasses import dataclass
from types import new_class
from typing import Any, Callable, Coroutine, Generic, Iterable, Protocol, cast, overload

from .address import Address, new_address
from .message import Message
from .validation import sniff_type_adapter
from .types import E, ParamsT, R, S, T
from .parameters import ParametersFactory
from .schema import Schema, sniff_content_type


class OperationProtocol(Generic[ParamsT, T, R, E], Protocol):
    def handle(
        self, request: Message[BaseOperation[S, ParamsT, T, R, E]]
    ) -> Coroutine[Any, Any, None]: ...


@dataclass
class ExceptionFormatter(Generic[E]):
    origin: type[BaseException]
    code: int
    description: str
    fmt: Callable[[BaseException], E] | None = None


def format_error(
    origin: type[BaseException],
    code: int,
    description: str,
    fmt: Callable[[BaseException], E] | None = None,
) -> ExceptionFormatter[E]:
    return ExceptionFormatter(origin, code, description, fmt)


class OperationSpec(Generic[S, ParamsT, T, R, E]):
    """Endpoint specification."""

    def __init__(
        self,
        address: str,
        name: str,
        parameters: ParametersFactory[S, ParamsT],
        payload: Schema[T],
        reply_payload: Schema[R],
        error: Schema[E],
        catch: Iterable[ExceptionFormatter[E]] | None = None,
        metadata: dict[str, Any] | None = None,
        status_code: int = 200,
    ) -> None:
        self.address = cast(Address[ParamsT], new_address(address, parameters))  # type: ignore
        self.name = name
        self.parameters = parameters
        self.payload = payload
        self.reply_payload = reply_payload
        self.error = error
        self.catch = catch or []
        self.metadata = metadata or {}
        self.status_code = status_code


@dataclass
class OperationRequest(Generic[ParamsT, T, R, E]):
    """Endpoint request."""

    subject: str
    params: ParamsT
    payload: T
    spec: OperationSpec[Any, ParamsT, T, R, E]


class BaseOperation(Generic[S, ParamsT, T, R, E], metaclass=abc.ABCMeta):
    _spec: OperationSpec[S, ParamsT, T, R, E]

    def __init_subclass__(
        cls, spec: OperationSpec[S, ParamsT, T, R, E] | None = None
    ) -> None:
        super().__init_subclass__()
        if not hasattr(cls, "_spec") and spec is None:
            raise TypeError("Missing spec")
        if not spec:
            return
        cls._spec = spec

    @abc.abstractmethod
    def handle(
        self, request: Message[BaseOperation[S, ParamsT, T, R, E]]
    ) -> Coroutine[Any, Any, None]:
        raise NotImplementedError

    @property
    def spec(self) -> OperationSpec[S, ParamsT, T, R, E]:
        return self._spec

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, None, None, R, E]],
    ) -> OperationRequest[ParamsT, T, R, E]: ...

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, None, T, R, E]], data: T
    ) -> OperationRequest[ParamsT, T, R, E]: ...

    @overload
    @classmethod
    def request(
        cls: type[OperationSpec[S, ParamsT, None, R, E]],
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> OperationRequest[ParamsT, T, R, E]: ...

    @overload
    @classmethod
    def request(
        cls, data: T, *args: S.args, **kwargs: S.kwargs
    ) -> OperationRequest[ParamsT, T, R, E]: ...

    @classmethod
    def request(
        cls, data: Any = ..., *args: Any, **kwargs: Any
    ) -> OperationRequest[ParamsT, T, R, E]:
        spec = cls._spec  # pyright: ignore[reportGeneralTypeIssues]
        if data is ...:
            if spec.payload.type is not type(None):
                raise TypeError("Missing request data")
        params = spec.parameters(*args, **kwargs)
        subject = spec.address.get_subject(params)
        return OperationRequest(
            subject=subject,
            params=params,
            payload=data,
            spec=spec,
        )


class OperationDecorator(Generic[S, ParamsT, T, R, E]):
    def __init__(
        self,
        address: str,
        parameters: ParametersFactory[S, ParamsT],
        request: Schema[T],
        response: Schema[R],
        error: Schema[E],
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        catch: Iterable[ExceptionFormatter[E]] | None = None,
        status_code: int = 200,
    ) -> None:
        self.address = address
        self.name = name
        self.parameters = parameters
        self.request = request
        self.response = response
        self.error = error
        self.metadata = metadata or {}
        self.catch = catch or []
        self.status_code = status_code

    @overload
    def __call__(
        self,
        cls: type[OperationProtocol[ParamsT, T, R, E]],
    ) -> type[BaseOperation[S, ParamsT, T, R, E]]: ...

    @overload
    def __call__(
        self,
        cls: type[object],
    ) -> type[BaseOperation[S, ParamsT, T, R, E]]: ...

    def __call__(self, cls: type[Any]) -> type[BaseOperation[S, ParamsT, T, R, E]]:
        name = self.name or cls.__name__
        spec = OperationSpec(
            address=self.address,
            name=name,
            parameters=self.parameters,
            payload=self.request,
            reply_payload=self.response,
            error=self.error,
            metadata=self.metadata,
            catch=self.catch,
            status_code=self.status_code,
        )
        new_cls = new_class(cls.__name__, (cls, BaseOperation), kwds={"spec": spec})
        return cast(type[BaseOperation[S, ParamsT, T, R, E]], new_cls)


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: None = None,
    reply_payload: type[R] | Schema[R],
    error: None = None,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[None]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[Any, None, None, R, None]: ...


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: None = None,
    reply_payload: type[R] | Schema[R],
    error: type[E] | Schema[E],
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[E]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[Any, None, None, R, E]: ...


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: type[T] | Schema[T],
    reply_payload: type[R] | Schema[R],
    error: None = None,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[None]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[Any, None, T, R, None]: ...


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: type[T] | Schema[T],
    reply_payload: type[R] | Schema[R],
    error: type[E] | Schema[E],
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[E]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[Any, None, T, R, E]: ...


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: None = None,
    reply_payload: type[R] | Schema[R],
    error: type[E] | Schema[E],
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[E]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[S, ParamsT, None, R, E]: ...


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: type[T] | Schema[T],
    reply_payload: None = None,
    error: type[E] | Schema[E],
    name: str | None = None,
    catch: Iterable[ExceptionFormatter[E]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[S, ParamsT, T, None, E]: ...


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: type[T] | Schema[T],
    reply_payload: type[R] | Schema[R],
    error: None = None,
    name: str | None = None,
    catch: Iterable[ExceptionFormatter[None]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[S, ParamsT, T, R, None]: ...


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: type[T] | Schema[T],
    reply_payload: type[R] | Schema[R],
    error: type[E] | Schema[E],
    name: str | None = None,
    catch: Iterable[ExceptionFormatter[E]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[S, ParamsT, T, R, E]: ...


def operation(
    address: str,
    *,
    parameters: Any = type(None),
    payload: Any = type(None),
    reply_payload: Any = type(None),
    error: Any = type(None),
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[Any]] | None = None,
    status_code: int = 200,
) -> OperationDecorator[Any, Any, Any, Any, Any]:
    if not isinstance(payload, Schema):
        payload = Schema(
            type=payload,
            content_type=sniff_content_type(payload),
            type_adapter=sniff_type_adapter(payload),
        )
    if not isinstance(reply_payload, Schema):
        reply_payload = Schema(
            type=reply_payload,
            content_type=sniff_content_type(reply_payload),
            type_adapter=sniff_type_adapter(reply_payload),
        )
    if not isinstance(error, Schema):
        error = Schema(
            type=error,
            content_type=sniff_content_type(error),
            type_adapter=sniff_type_adapter(error),
        )
    return OperationDecorator(
        address=address,
        parameters=parameters,
        request=payload,  # pyright: ignore[reportUnknownArgumentType]
        response=reply_payload,  # pyright: ignore[reportUnknownArgumentType]
        error=error,  # pyright: ignore[reportUnknownArgumentType]
        name=name,
        metadata=metadata,
        catch=catch,
        status_code=status_code,
    )
