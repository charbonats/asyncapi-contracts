from __future__ import annotations

from contracts.client import Client

from ..components.my_consumer import MyEvent, MyEventData


class MyProducer:
    """An example of producer.

    This producer does not depend on a specific message broker.
    Instead it relies on the abstract client interface to publish
    events to the underlying  message broker.
    """

    def __init__(self, client: Client) -> None:
        self.client = client

    async def produce(self) -> None:
        await self.client.send(
            MyEvent.publish(
                location="kitchen",
                device_id="thermometer",
                data=MyEventData(temperature=23.5, timestamp=123456),
            )
        )
