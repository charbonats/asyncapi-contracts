from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from .types import T, TypeAdapter


@dataclass
class Schema(Generic[T]):
    """Schema type.

    Args:
        type: The type of the schema.
        content_type: The content type of the schema.
        type_adapter: The type adapter for the schema.
    """

    type: type[T]
    content_type: str
    type_adapter: TypeAdapter[T]
