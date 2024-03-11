from __future__ import annotations

from dataclasses import is_dataclass
from types import new_class
from typing import Any, Callable, Generic, Iterable, cast, overload

from .abc.consumer import BaseConsumer
from .abc.event import BaseEvent
from .abc.operation import BaseOperation
from .core.event_spec import EventSpec
from .core.exception_formatter import ExceptionFormatter
from .core.operation_spec import OperationSpec
from .core.schema import Schema
from .core.application_info import Tag, License, Contact
from .core.types import ParametersFactory, ParamsT, R, S, T, TypeAdapter

from .backends.type_adapter.defaults import sniff_type_adapter


def license(name: str | None = None, url: str | None = None) -> License:
    """Create a new license."""
    return License(name, url)


def tag(
    name: str, description: str | None = None, external_docs: str | None = None
) -> Tag:
    """Create a new tag."""
    return Tag(name, description, external_docs)


def contact(
    name: str | None = None, url: str | None = None, email: str | None = None
) -> Contact:
    """Create a new contact."""
    return Contact(name, url, email)


def exception(
    origin: type[BaseException],
    code: int,
    description: str,
    fmt: Callable[[BaseException], R] | None = None,
) -> ExceptionFormatter[R]:
    return ExceptionFormatter(origin, code, description, fmt)


def schema(
    type: type[T],
    content_type: str | None = None,
    type_adapter: TypeAdapter[T] | None = None,
) -> Schema[T]:
    """Create a schema for the given type.

    Args:
        type: The type of the schema.
        content_type: The content type of the schema.
        type_adapter: The type adapter for the schema.

    Returns:
        The schema for the given type.
    """
    if not content_type:
        content_type = _sniff_content_type(type)
    if not type_adapter:
        type_adapter = sniff_type_adapter(type)
    return Schema(type, content_type, type_adapter)


def _sniff_content_type(typ: type[Any]) -> str:
    """Sniff the content type for the given type.

    Args:
        typ: The type to sniff the content type for.

    Returns:
        The content type for the given type.
    """
    if is_dataclass(typ):
        return "application/json"
    if hasattr(typ, "model_fields"):
        return "application/json"
    if hasattr(typ, "__fields__"):
        return "application/json"
    if typ is type(None):
        return ""
    if typ is str:
        return "text/plain"
    if typ is int:
        return "text/plain"
    if typ is float:
        return "text/plain"
    if typ is bytes:
        return "application/octet-stream"
    if typ is dict:
        return "application/json"
    if typ is list:
        return "application/json"
    raise TypeError(
        f"Cannot guess content-type for class {typ}. "
        "Please specify the content-type explicitly."
    )


class _EventDecorator(Generic[S, ParamsT, T]):
    def __init__(
        self,
        address: str,
        parameters: ParametersFactory[S, ParamsT],
        payload: Schema[T],
    ) -> None:
        self.address = address
        self.parameters = parameters
        self.payload = payload

    def __call__(self, cls: type[Any]) -> type[BaseEvent[S, ParamsT, T]]:
        spec = EventSpec(
            name=cls.__name__,
            address=self.address,
            parameters=self.parameters,
            payload=self.payload,
            metadata={},
        )
        new_cls = new_class(cls.__name__, (cls, BaseEvent), kwds={"spec": spec})
        return cast(type[BaseEvent[S, ParamsT, T]], new_cls)


def event(
    address: str,
    parameters: ParametersFactory[S, ParamsT],
    payload_schema: Schema[T] | type[T],
) -> _EventDecorator[S, ParamsT, T]:
    if not isinstance(payload_schema, Schema):
        payload_schema = Schema(
            type=payload_schema,
            content_type=_sniff_content_type(payload_schema),
            type_adapter=sniff_type_adapter(payload_schema),
        )
    return _EventDecorator(address, parameters, payload_schema)


class _ConsumerDecorator(Generic[S, ParamsT, T]):
    def __init__(self, source: type[BaseEvent[S, ParamsT, T]]) -> None:
        self.source = source

    def __call__(self, cls: type[Any]) -> type[BaseConsumer[S, ParamsT, T]]:
        new_cls = new_class(
            cls.__name__, (cls, BaseConsumer), kwds={"source": self.source}
        )
        return cast(type[BaseConsumer[S, ParamsT, T]], new_cls)


def consumer(
    source: type[BaseEvent[S, ParamsT, T]],
) -> _ConsumerDecorator[S, ParamsT, T]:
    return _ConsumerDecorator(source)


class _OperationDecorator(Generic[S, ParamsT, T, R]):
    def __init__(
        self,
        address: str,
        parameters: ParametersFactory[S, ParamsT],
        request: Schema[T],
        response: Schema[R],
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        catch: Iterable[ExceptionFormatter[R]] | None = None,
        status_code: int = 200,
    ) -> None:
        self.address = address
        self.name = name
        self.parameters = parameters
        self.request = request
        self.response = response
        self.metadata = metadata or {}
        self.catch = catch or []
        self.status_code = status_code

    def __call__(self, cls: type[Any]) -> type[BaseOperation[S, ParamsT, T, R]]:
        name = self.name or cls.__name__
        spec = OperationSpec(
            address=self.address,
            name=name,
            parameters=self.parameters,
            payload=self.request,
            reply_payload=self.response,
            metadata=self.metadata,
            catch=self.catch,
            status_code=self.status_code,
        )
        new_cls = new_class(cls.__name__, (cls, BaseOperation), kwds={"spec": spec})
        return cast(type[BaseOperation[S, ParamsT, T, R]], new_cls)


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: None = None,
    reply_payload: None = None,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[R]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[Any, None, None, None]:
    ...
    # No parameters


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: None = None,
    reply_payload: type[R] | Schema[R],
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[R]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[Any, None, None, R]:
    ...
    # Only reply


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: type[T] | Schema[T],
    reply_payload: None = None,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[None]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[Any, None, T, None]:
    ...
    # Only payload


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: None = None,
    reply_payload: None = None,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[None]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[S, ParamsT, None, None]:
    ...
    # Only params


@overload
def operation(
    address: str,
    *,
    parameters: None = None,
    payload: type[T] | Schema[T],
    reply_payload: type[R] | Schema[R],
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[R]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[Any, None, T, R]:
    ...
    # Payload + reply


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: None = None,
    reply_payload: type[R] | Schema[R],
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[R]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[S, ParamsT, None, R]:
    ...
    # Params + reply


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: type[T] | Schema[T],
    reply_payload: None = None,
    name: str | None = None,
    catch: Iterable[ExceptionFormatter[None]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[S, ParamsT, T, None]:
    ...
    # Params + payload


@overload
def operation(
    address: str,
    *,
    parameters: ParametersFactory[S, ParamsT],
    payload: type[T] | Schema[T],
    reply_payload: type[R] | Schema[R],
    name: str | None = None,
    catch: Iterable[ExceptionFormatter[R]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[S, ParamsT, T, R]:
    ...
    # Params + payload + reply


def operation(
    address: str,
    *,
    parameters: Any = type(None),
    payload: Any = type(None),
    reply_payload: Any = type(None),
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
    catch: Iterable[ExceptionFormatter[Any]] | None = None,
    status_code: int = 200,
) -> _OperationDecorator[Any, Any, Any, Any]:
    if not isinstance(payload, Schema):
        payload = Schema(
            type=payload,
            content_type=_sniff_content_type(payload),
            type_adapter=sniff_type_adapter(payload),
        )
    if not isinstance(reply_payload, Schema):
        reply_payload = Schema(
            type=reply_payload,
            content_type=_sniff_content_type(reply_payload),
            type_adapter=sniff_type_adapter(reply_payload),
        )
    return _OperationDecorator(
        address=address,
        parameters=parameters,
        request=payload,  # pyright: ignore[reportUnknownArgumentType]
        response=reply_payload,  # pyright: ignore[reportUnknownArgumentType]
        name=name,
        metadata=metadata,
        catch=catch,
        status_code=status_code,
    )
