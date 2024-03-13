from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic

from .types import R


@dataclass
class ExceptionFormatter(Generic[R]):
    """Exception formatter."""

    origin: type[BaseException]
    code: int
    description: str
    fmt: Callable[[BaseException], R] | None = None
