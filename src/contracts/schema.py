from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from typing import Any, Generic

from .validation import TypeAdapter, sniff_type_adapter
from .types import T


@dataclass
class Schema(Generic[T]):
    """Schema type."""

    type: type[T]
    content_type: str
    type_adapter: TypeAdapter[T]


def schema(
    type: type[T],
    content_type: str | None = None,
    type_adapter: TypeAdapter[T] | None = None,
) -> Schema[T]:
    if not content_type:
        content_type = sniff_content_type(type)
    if not type_adapter:
        type_adapter = sniff_type_adapter(type)
    return Schema(type, content_type, type_adapter)


def sniff_content_type(typ: type[Any]) -> str:
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
