from __future__ import annotations
from typing import Generic, Protocol

from .types import S, P


class ParametersFactory(Generic[S, P], Protocol):
    """A factory for creating parameters.

    Given a signature S, create parameters of type P.
    """

    def __call__(
        self,
        *args: S.args,
        **kwargs: S.kwargs,
    ) -> P: ...
