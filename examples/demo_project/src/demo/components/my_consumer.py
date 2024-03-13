from __future__ import annotations

from dataclasses import dataclass

from contracts import consumer, event


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


@consumer(source=MyEvent)
class MyConsumer:
    """An example consumer."""
