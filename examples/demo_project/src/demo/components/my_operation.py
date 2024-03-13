from __future__ import annotations

from dataclasses import dataclass

from contracts import exception, operation


@dataclass
class MyParams:
    """Parameters found in endpoint request subject."""

    device_id: str


@dataclass
class MyRequest:
    """Fields expected in endpoint request payload."""

    value: int


@dataclass
class MyResponse:
    """Fields expected in endpoint reply payload."""

    success: bool
    result: int


@operation(
    address="foo.{device_id}",
    parameters=MyParams,
    payload=MyRequest,
    reply_payload=MyResponse,
    catch=[
        exception(
            ValueError,
            400,
            "Bad request",
            lambda _: MyResponse(False, 0),
        ),
    ],
)
class MyOperation:
    """This is an example operation definition."""
