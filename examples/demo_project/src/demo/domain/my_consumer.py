from __future__ import annotations

from contracts import Message

from ..components.my_consumer import MyConsumer, MyEvent


class MyConsumerImpl(MyConsumer):
    """An example of a consumer implementation."""

    async def handle(self, event: Message[MyEvent]) -> None:
        print(f"Consuming event headers: {event.headers()}")
        print(f"Consuming event payload: {event.payload()}")
        await event.ack()
