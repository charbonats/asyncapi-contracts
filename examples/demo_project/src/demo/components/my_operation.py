from __future__ import annotations

from dataclasses import dataclass

from contracts import exception, operation


@dataclass
class MyParams:
    """Parameters found in operation request subject."""

    device_id: str


@dataclass
class MyOptions:
    """Fields expected in operation request payload."""

    value: int


@dataclass
class MyResult:
    """Fields expected in operation reply payload."""

    success: bool
    value: int


@operation(
    address="foo.{device_id}",
    parameters=MyParams,
    payload=MyOptions,
    reply_payload=MyResult,
    catch=[
        exception(
            ValueError,
            400,
            "Bad request",
            lambda _: MyResult(False, 0),
        ),
    ],
)
class MyOperation:
    """This is an example operation definition."""
