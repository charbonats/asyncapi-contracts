from __future__ import annotations

from demo.components.my_operation import MyOperation, MyOptions
from nats import connect

from contracts.backends.client.micro import Client as MicroClient
from contracts.client import Client, OperationError


async def do_request(
    client: Client,
) -> None:
    """An example function to send a request to a micro service."""
    # An exception will be raised if the request fails.
    reply = await client.send(
        MyOperation.request(
            MyOptions(value=2),
            device_id="123",
            headers={"foo": "bar"},
        ),
        timeout=2.5,
    )
    data = reply.data()
    print(data)
    headers = reply.headers()
    print(headers)


async def do_request_with_error_handling(
    client: Client,
) -> None:
    """An example function to send a request to a micro service."""
    request = MyOperation.request(
        MyOptions(value=2),
        device_id="123",
        headers={"foo": "bar"},
    )
    try:
        reply = await client.send(
            request,
            timeout=2.5,
        )
        data = reply.data()
        print(data)
        headers = reply.headers()
        print(headers)
    except OperationError as e:
        print(e.code)
        print(e.description)
        print(e.headers)
        # Error data is not parsed into an object
        print(e.raw_data.decode())
        # But it can be decoded easily using the client
        data = client.decode_error(request, e)
        print(data)


async def do_request_without_raising_exception(
    client: Client,
) -> None:
    """An example function to send a request to a micro service."""
    reply = await client.send(
        MyOperation.request(
            MyOptions(value=2),
            device_id="123",
            headers={"foo": "bar"},
        ),
        timeout=2.5,
        raise_on_error=False,
    )
    if reply.is_error():
        data = reply.error_data()
        print(data)
        headers = reply.headers()
        print(headers)
        print(reply.error_code())
        print(reply.error_description())
    else:
        data = reply.data()
        print(data)
        headers = reply.headers()
        print(headers)


async def main() -> None:
    """An example main function to send a request to a micro service."""
    nc = await connect()
    client = MicroClient(nc)
    await do_request(client)
    await do_request_with_error_handling(client)
    await do_request_without_raising_exception(client)
