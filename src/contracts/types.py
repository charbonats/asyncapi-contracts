"""The types module defines several generic type variables for
use in the contracts package.
"""

from __future__ import annotations

from typing import TypeVar

from typing_extensions import ParamSpec

T = TypeVar("T")
R = TypeVar("R")
E = TypeVar("E")

ParamsT = TypeVar("ParamsT")
S = ParamSpec("S")

P = TypeVar("P", covariant=True)
