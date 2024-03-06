from __future__ import annotations


from dataclasses import dataclass

from contracts import event, consumer, Event
from contracts.interfaces import Client


@dataclass
class MyEventData:
    temperature: float
    timestamp: int


@dataclass
class MyEventParams:
    location: str
    device_id: str


@event(
    address="sensors.{location}.{device_id}",
    parameters=MyEventParams,
    payload_schema=MyEventData,
)
class MyEvent:
    """An example event."""


# Consumers are just like operations
# They must be defined first
# And then implemented
@consumer(source=MyEvent)
class MyConsumer:
    """An example consumer."""


# An implementation of a consumer is similar to an operation
# This does not belong here, but it's just an example
class MyConsumerImpl(MyConsumer):
    async def handle(self, event: Event[MyEvent]) -> None:
        print(f"Consuming event headers: {event.headers()}")
        print(f"Consuming event payload: {event.payload()}")
        await event.ack()


# Example of a producer (this does not belong here but it's just an example)
# Producers are a bit difficult to document, because they can
# publish messages from almost anywhere in the app
# IMHO it's better to document the producer once in the application
# itself purely for the sake of the reader. Else we introduce a Publisher
# class that is not really useful in the application itself.
class MyProducer:
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
