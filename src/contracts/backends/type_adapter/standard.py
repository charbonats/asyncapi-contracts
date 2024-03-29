from __future__ import annotations

import datetime
import json
import numbers
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from contracts.core.types import T, TypeAdapter, TypeAdapterFactory


class RawTypeAdapter(TypeAdapter[T]):
    """A type adapter using standard library."""

    def __init__(self, typ: type[T]) -> None:
        self.typ = typ

    def encode(self, message: T) -> bytes:
        if self.typ is type(None):
            if message:
                raise ValueError("No value expected")
            return b""
        if isinstance(message, bytes):
            return message
        return str(message).encode("utf-8")

    def decode(self, data: bytes) -> T:
        if self.typ is bytes:
            return data  # type: ignore
        if self.typ is type(None):
            if data:
                raise ValueError("No value expected")
            return None  # type: ignore
        return self.typ(data.decode("utf-8"))


class RawTypeAdapterFactory(TypeAdapterFactory):
    """A type adapter factory using standard library."""

    def __call__(self, schema: type[T]) -> TypeAdapter[T]:
        return RawTypeAdapter(schema)


class StandardJSONAdapter(TypeAdapter[T]):
    """A type adapter using standard library."""

    def __init__(self, typ: type[T]) -> None:
        self.typ = typ

    def encode(self, message: T) -> bytes:
        if self.typ is type(None):
            if message:
                raise ValueError("No value expected")
            return b""
        return json.dumps(
            message,
            default=_default_serializer,
            separators=(",", ":"),
        ).encode("utf-8")

    def decode(self, data: bytes) -> T:
        if self.typ is type(None):
            if data:
                raise ValueError("No value expected")
            return None  # type: ignore
        result = json.loads(data)
        try:
            return self.typ(**result)
        except TypeError as exc:
            raise ValueError("Failed to decode data") from exc


class StandardJSONAdapterFactory(TypeAdapterFactory):
    """A type adapter factory using standard library."""

    def __call__(self, schema: type[T]) -> TypeAdapter[T]:
        return StandardJSONAdapter(schema)


def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, (bytes, bytearray, set)):
        return list(obj)  # pyright: ignore[reportUnknownArgumentType]
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, numbers.Integral):
        return int(obj)
    if isinstance(obj, numbers.Real):
        return float(obj)
    raise TypeError
