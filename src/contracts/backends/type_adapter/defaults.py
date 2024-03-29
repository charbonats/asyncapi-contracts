from __future__ import annotations

from dataclasses import is_dataclass

from contracts.core.types import T, TypeAdapter, TypeAdapterFactory


def default_json_adapter() -> TypeAdapterFactory:
    try:
        import pydantic
    except ImportError:
        from .standard import StandardJSONAdapterFactory

        return StandardJSONAdapterFactory()

    if pydantic.__version__.startswith("1."):
        from .pydantic_v1 import PydanticV1JSONAdapterFactory

        return PydanticV1JSONAdapterFactory()
    elif pydantic.__version__.startswith("2."):
        from .pydantic_v2 import PydanticV2JSONAdapterFactory

        return PydanticV2JSONAdapterFactory()

    raise ImportError("Cannot find a suitable pydantic version.")


def sniff_type_adapter(typ: type[T]) -> TypeAdapter[T]:
    from .standard import RawTypeAdapter

    if typ is bytes:
        return RawTypeAdapter(typ)
    if typ is str:
        return RawTypeAdapter(typ)
    if typ is int:
        return RawTypeAdapter(typ)
    if typ is float:
        return RawTypeAdapter(typ)
    if typ is bool:
        return RawTypeAdapter(typ)
    if typ is type(None):
        return RawTypeAdapter(typ)
    if is_dataclass(typ):
        return default_json_adapter()(typ)
    if hasattr(typ, "model_fields"):
        return default_json_adapter()(typ)
    if hasattr(typ, "__fields__"):
        return default_json_adapter()(typ)
    raise TypeError(f"Cannot find a type adapter for the given type: {typ}")
