"""The types module defines several generic type variables for
use in the contracts package.
"""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
R = TypeVar("R")

ParamsT = TypeVar("ParamsT")
S = ParamSpec("S")

P = TypeVar("P", covariant=True)


class ParametersFactory(Generic[S, P], Protocol):
    """A factory for creating parameters.

    Given a signature S, create parameters of type P.
    """

    def __call__(
        self,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> P:
        ...


class TypeAdapter(Protocol, Generic[T]):
    """A type adapter is a class providing methods to encode and decode data."""

    def encode(self, message: T) -> bytes:
        ...

    def decode(self, data: bytes) -> T:
        ...


class TypeAdapterFactory(Protocol):
    """A type adapter factory is a class providing methods to create type adapters."""

    def __call__(self, schema: type[T]) -> TypeAdapter[T]:
        ...
