from __future__ import annotations

from nats import connect
from contracts.interfaces import Client, OperationError
from contracts.backends.micro import Client as MicroClient

from demo.contract.my_endpoint import MyEndpoint, MyRequest


async def do_request(
    client: Client,
) -> None:
    """An example function to send a request to a micro service."""
    # This will not raise an error if the reply received indicates
    # an error through the status code
    response = await client.send(
        MyEndpoint.request(MyRequest(value=2), "123"),
        headers={"foo": "bar"},
        timeout=2.5,
    )
    # 3. Get the data
    # This will raise an error if the reply received indicates an
    # error through the status code
    try:
        data = response.data()
        print(data)
    except OperationError:
        # You can access the decoded error in such case
        error = response.error()
        print(error)
    # 4. Headers can always be accessed, even if the reply is an error
    headers = response.headers()
    print(headers)


async def main() -> None:
    """An example main function to send a request to a micro service."""
    nc = await connect()
    client = MicroClient(nc)
    await do_request(client)
