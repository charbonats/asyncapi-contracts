from __future__ import annotations
from typing import Generic, Protocol

from .types import S, P


class ParametersFactory(Generic[S, P], Protocol):
    def __call__(
        self,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> P:
        ...
