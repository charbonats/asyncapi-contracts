from __future__ import annotations

from dataclasses import dataclass

from contracts import format_error, operation


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

    result: int


@operation(
    address="foo.{device_id}",
    parameters=MyParams,
    request_schema=MyRequest,
    response_schema=MyResponse,
    error_schema=str,
    catch=[
        format_error(
            ValueError,
            400,
            "Bad request",
            lambda err: "Request failed due to malformed request data",
        ),
    ],
)
class MyOperation:
    """This is an example operation definition."""
